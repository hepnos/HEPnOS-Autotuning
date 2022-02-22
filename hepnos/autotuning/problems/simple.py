import sys
import os
import argparse
import mochi.bedrock.spec as brk
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


__default_params = {
    'HEPNOS_DATASET': 'nova',
    'HEPNOS_LABEL': 'abc',
    'HEPNOS_ENABLE_PROFILING': 0,
    'HEPNOS_UTILITY_TIMEOUT': 30,
    'HEPNOS_LOADER_DATAFILE': '$EXPDIR/$HEPNOS_EXP_PLATFORM-50files.txt',
    'HEPNOS_LOADER_VERBOSE': 'critical',
    'HEPNOS_LOADER_PRODUCTS': [
        'hep::rec_energy_numu',
        'hep::rec_hdr',
        'hep::rec_sel_contain',
        'hep::rec_sel_cvn2017',
        'hep::rec_sel_cvnProd3Train',
        'hep::rec_sel_remid',
        'hep::rec_slc',
        'hep::rec_spill',
        'hep::rec_trk_cosmic',
        'hep::rec_trk_kalman',
        'hep::rec_trk_kalman_tracks',
        'hep::rec_vtx',
        'hep::rec_vtx_elastic_fuzzyk',
        'hep::rec_vtx_elastic_fuzzyk_png',
        'hep::rec_vtx_elastic_fuzzyk_png_cvnpart',
        'hep::rec_vtx_elastic_fuzzyk_png_shwlid' ],
    'HEPNOS_LOADER_ENABLE_PROFILING': 0,
    'HEPNOS_LOADER_SOFT_TIMEOUT': 10000,
    'HEPNOS_LOADER_TIMEOUT': 300,
    'HEPNOS_PEP_VERBOSE': 'info',
    'HEPNOS_PEP_PRODUCTS': [
        'hep::rec_energy_numu',
        'hep::rec_hdr',
        'hep::rec_sel_contain',
        'hep::rec_sel_cvn2017',
        'hep::rec_sel_cvnProd3Train',
        'hep::rec_sel_remid',
        'hep::rec_slc',
        'hep::rec_spill',
        'hep::rec_trk_cosmic',
        'hep::rec_trk_kalman',
        'hep::rec_trk_kalman_tracks',
        'hep::rec_vtx',
        'hep::rec_vtx_elastic_fuzzyk',
        'hep::rec_vtx_elastic_fuzzyk_png',
        'hep::rec_vtx_elastic_fuzzyk_png_cvnpart',
        'hep::rec_vtx_elastic_fuzzyk_png_shwlid' ],
    'HEPNOS_PEP_ENABLE_PROFILING':0,
    'HEPNOS_PEP_TIMEOUT': 300,
    'CONST_TIMEOUT': 99999999,
    'CONST_FAILURE': 88888888
}


def __generate_settings(wdir, nodes_per_exp, disable_pep, **kwargs):
    """Generate the settings.sh file using default parameters."""
    with open(f'{wdir}/settings.sh', 'w+') as f:
        for k, v in __default_params.items():
            f.write(f'{k}=')
            if v is None:
                continue
            if isinstance(v, list):
                s = '('
                for e in v:
                    s += f'\n\t{e}'
                s += ')'
                f.write(s+'\n')
            else:
                f.write(str(v)+'\n')
        f.write(f'NODES_PER_EXP={nodes_per_exp}\n')
        if disable_pep:
            f.write('DISABLE_PEP=true\n')
        else:
            f.write('DISABLE_PEP=false\n')


def __generate_hepnos_config(wdir, protocol, busy_spin,
                             hepnos_progress_thread,
                             hepnos_num_rpc_threads,
                             hepnos_num_event_databases,
                             hepnos_num_product_databases,
                             hepnos_num_providers,
                             hepnos_pool_type,
                             hepnos_pes_per_node,
                             hepnos_nodelist,
                             **kwargs):
    """Generate a JSON configuration for Bedrock to deploy HEPnOS."""
    proc_spec = brk.ProcSpec(margo=protocol)
    # Add yokan library
    proc_spec.libraries['yokan'] = 'libyokan-bedrock-module.so'
    # Setup busy-spinning if requested
    if busy_spin:
        proc_spec.margo.mercury.na_no_block = True
    # Add SSG group
    proc_spec.ssg.add(name='hepnos', bootstrap='mpi', group_file=f'{wdir}/hepnos.ssg',
                      pool=proc_spec.margo.argobots.pools[0],
                      swim=brk.SwimSpec(disabled=True))
    # Add progress xstream if requested
    if hepnos_progress_thread:
        progress_pool = proc_spec.margo.argobots.pools.add(
            name='__progress__', kind='fifo_wait', access='mpmc')
        proc_spec.margo.progress_pool = progress_pool
        progress_es = proc_spec.margo.argobots.xstreams.add(
            name='__progress__',
            scheduler=brk.SchedulerSpec(pools=[progress_pool]))
    # Setup additional pools
    rpc_pools = []
    if hepnos_num_rpc_threads > 0 or hepnos_progress_thread:
        for i in range(hepnos_num_providers):
            rpc_pool = proc_spec.margo.argobots.pools.add(
                name=f'__rpc_pool_{i}__', kind=hepnos_pool_type, access='mpmc')
            rpc_pools.append(rpc_pool)
    else:
        rpc_pools = [proc_spec.margo.argobots.pools[0]]
    # Setup additional xstreams
    for i in range(hepnos_num_rpc_threads):
        pools = []
        if hepnos_num_rpc_threads < hepnos_num_providers:
            j = i
            while j < len(rpc_pools):
                pools.append(rpc_pools[j])
                j += hepnos_num_rpc_threads
        else:
            pools = [rpc_pools[i % hepnos_num_providers]]
        proc_spec.margo.argobots.xstreams.add(
            name=f'__rpc_es_{i}__', scheduler=brk.SchedulerSpec(pools=pools))
    if hepnos_num_rpc_threads == 0 and hepnos_progress_thread:
        proc_spec.margo.argobots.xstreams[0].scheduler.pools.extend(rpc_pools)
    # Create databases
    dbs = []
    dbs.append({ "name": 'hepnos-datasets-0', "type": 'map', "config": {} })
    dbs.append({ "name": 'hepnos-runs-0', "type": 'set', "config": {} })
    dbs.append({ "name": 'hepnos-subruns-0', "type": 'set', "config": {} })
    for i in range(hepnos_num_event_databases):
        dbs.append({ "name": f'hepnos-events-{i}', "type": 'set', "config": {} })
    for i in range(hepnos_num_product_databases):
        dbs.append({ "name": f'hepnos-products-{i}', "type": 'map', "config": {} })
    # Setup providers
    providers = []
    for i in range(hepnos_num_providers):
        proc_spec.providers.add(name=f'hepnos_{i}',
                                type='yokan', pool=rpc_pools[i % len(rpc_pools)],
                                provider_id=i+1,
                                config={'databases': []})
    # Bind databases to providers
    for i, db in enumerate(dbs):
        proc_spec.providers[int(i%hepnos_num_providers)].config['databases'].append(db)
    # Generate configuration
    with open(f'{wdir}/hepnos.json', 'w+') as config:
        config.write(proc_spec.to_json(indent=4))
    # Generate settings.sh
    with open(f'{wdir}/settings.sh', 'a+') as params:
        params.write(f'HEPNOS_PES_PER_NODE={hepnos_pes_per_node}\n')
        params.write(f'NODES_FOR_HEPNOS={hepnos_nodelist}\n')


def __generate_loader_config(wdir, protocol, busy_spin,
                             loader_progress_thread,
                             loader_batch_size,
                             loader_pes_per_node,
                             loader_async,
                             loader_async_threads,
                             loader_nodelist,
                             **kwargs):
    """Generate configuration for the Dataloader."""
    margo_spec = brk.MargoSpec(mercury=protocol)
    if busy_spin:
        margo_spec.mercury.na_no_block = True
    if loader_progress_thread:
        pool = margo_spec.argobots.pools.add(name='__progress__')
        margo_spec.argobots.xstreams.add(
            name='__progress__',
            scheduler=brk.SchedulerSpec(pools=[pool]))
        margo_spec.progress_pool = pool
    # Generate configuration
    with open(f'{wdir}/dataloader.json', 'w+') as config:
        config.write(margo_spec.to_json(indent=4))
    # Generate settings.sh
    with open(f'{wdir}/settings.sh', 'a+') as params:
        if loader_async:
            params.write('HEPNOS_LOADER_ASYNC=-a\n')
            params.write(f'HEPNOS_LOADER_ASYNC_THREADS={loader_async_threads}\n')
        else:
            params.write('HEPNOS_LOADER_ASYNC=\n')
            params.write('HEPNOS_LOADER_ASYNC_THREADS=0\n')
        params.write(f'HEPNOS_LOADER_BATCH_SIZE={loader_batch_size}\n')
        params.write(f'HEPNOS_LOADER_PES_PER_NODE={loader_pes_per_node}\n')
        params.write(f'NODES_FOR_LOADER={loader_nodelist}\n')


def __generate_pep_config(wdir, protocol, busy_spin,
                          pep_progress_thread,
                          pep_num_threads,
                          pep_ibatch_size,
                          pep_obatch_size,
                          pep_pes_per_node,
                          pep_no_preloading,
                          pep_nodelist,
                          **kwargs):
    """Generate configuration for the Parallel Event Processing benchmark."""
    margo_spec = brk.MargoSpec(mercury=protocol)
    if busy_spin:
        margo_spec.mercury.na_no_block = True
    if pep_progress_thread:
        pool = margo_spec.argobots.pools.add(name='__progress__')
        margo_spec.argobots.xstreams.add(
            name='__progress__',
            scheduler=brk.SchedulerSpec(pools=[pool]))
        margo_spec.progress_pool = pool
    # Generate configuration
    with open(f'{wdir}/pep.json', 'w+') as config:
        config.write(margo_spec.to_json(indent=4))
    # Generate settings.sh
    with open(f'{wdir}/settings.sh', 'a+') as params:
        params.write(f'HEPNOS_PEP_THREADS={pep_num_threads}\n')
        params.write(f'HEPNOS_PEP_IBATCH_SIZE={pep_ibatch_size}\n')
        params.write(f'HEPNOS_PEP_OBATCH_SIZE={pep_obatch_size}\n')
        params.write(f'HEPNOS_PEP_PES_PER_NODE={pep_pes_per_node}\n')
        if pep_no_preloading:
            params.write('HEPNOS_PEP_PRELOAD=\n')
        else:
            params.write('HEPNOS_PEP_PRELOAD=--preload\n')
        params.write(f'NODES_FOR_PEP={pep_nodelist}\n')


def __add_parameter_to_parser(parser, name, type, default, domain, description):
    """Callback to add a parameter to an argparse parser."""
    if type == bool:
        parser.add_argument('--'+name, default=default, action='store_true', required=False,
                            help=description)
    else:
        parser.add_argument('--'+name, default=default, type=type, required=False,
                            help=description)


def __add_parameter_to_problem(problem, name, type, default, domain, description):
    """Callback to add a parameter to a DeepHyper problem."""
    problem.add_hyperparameter(domain, name, default_value=default)


def __fill_context(context, add_parameter, disable_pep=False, more_params=True):
    """Fill either an argparse parser or a DeepHyper problem using
    the provided add_parameter callback."""

    add_parameter(context, "busy_spin", bool, False, [True, False],
        "Whether Mercury should busy-spin instead of block")
    add_parameter(context, "hepnos_progress_thread", bool, False, [True, False],
        "Whether to use a dedicated progress thread in HEPnOS")
    add_parameter(context, "hepnos_num_rpc_threads", int, 0, (0, 63),
        "Number of threads used for serving RPC requests")
    add_parameter(context, "hepnos_num_event_databases", int, 1, (1, 16),
        "Number of databases per process used to store events")
    add_parameter(context, "hepnos_num_product_databases", int, 1, (1, 16),
        "Number of databases per process used to store products")
    add_parameter(context, "hepnos_num_providers", int, 1, (1, 32),
        "Number of database providers per process")
    add_parameter(context, "hepnos_pool_type", str, 'fifo_wait', ['fifo','fifo_wait'],
        "Thread-scheduling policity used by Argobots pools")
    add_parameter(context, "hepnos_pes_per_node", int, 2, [1, 2, 4, 8, 16, 32],
        "Number of HEPnOS processes per node")
    add_parameter(context, "loader_progress_thread", bool, False, [True, False],
        "Whether to use a dedicated progress thread in the Dataloader")
    add_parameter(context, "loader_batch_size", int, 512, (1, 2048, "log-uniform"),
        "Size of the batches of events sent by the Dataloader to HEPnOS")
    add_parameter(context, "loader_pes_per_node", int, 2, [1, 2, 4, 8, 16],
        "Number of processes per node for the Dataloader")
    if more_params:
        add_parameter(context, "loader_async", bool, False, [True, False],
            "Whether to use the HEPnOS AsyncEngine in the Dataloader")
        add_parameter(context, "loader_async_threads", int, 1, (1, 63, "log-uniform"),
            "Number of threads for the AsyncEngine to use")
    if disable_pep:
        return
    add_parameter(context, "pep_progress_thread", bool, False, [True, False],
        "Whether to use a dedicated progress thread in the PEP step")
    add_parameter(context, "pep_num_threads", int, 4, (1, 31),
        "Number of threads used for processing in the PEP step")
    add_parameter(context, "pep_ibatch_size", int, 128, (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are loading events from HEPnOS")
    add_parameter(context, "pep_obatch_size", int, 128, (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are exchanging events among themselves")
    add_parameter(context, "pep_pes_per_node", int, 8, [1, 2, 4, 8, 16, 32],
        "Number of processes per node for the PEP step")
    if more_params:
        add_parameter(context, "pep_no_preloading", bool, False, [True, False],
            "Whether to disable product-preloading in PEP")


def __generate_experiment_directory(wdir, protocol,
                                    hepnos_nodelist='',
                                    loader_nodelist='',
                                    pep_nodelist='',
                                    disable_pep=False,
                                    more_params=False,
                                    **kwargs):
    """Creates a directory for a new experiment and generate the
    configuration files for the various components."""
    exp_folder = os.path.dirname(__file__)+'/exp'
    from shutil import copytree
    copytree(exp_folder, wdir)
    if not more_params:
        kwargs['loader_async'] = False
        kwargs['loader_async_threads'] = 1
        kwargs['pep_no_preloading'] = False
    __generate_settings(wdir=wdir, disable_pep=disable_pep, **kwargs)
    __generate_hepnos_config(wdir=wdir, protocol=protocol, hepnos_nodelist=hepnos_nodelist, **kwargs)
    __generate_loader_config(wdir=wdir, protocol=protocol, loader_nodelist=loader_nodelist, **kwargs)
    if not disable_pep:
        __generate_pep_config(wdir=wdir, protocol=protocol, pep_nodelist=pep_nodelist, **kwargs)
    with open(f'{wdir}/settings.sh', 'a+') as params:
        if len(loader_nodelist) > 0:
            utility_node = loader_nodelist.split(',')[0]
        else:
            utility_node = ''
        params.write(f'NODES_FOR_UTILITY={utility_node}\n')


def run_instance(exp_prefix, build_prefix, protocol, nodes_per_exp, disable_pep, more_params, **kwargs):
    import uuid
    from shutil import rmtree
    exp_uuid = uuid.uuid4()
    wdir = exp_prefix + str(exp_uuid)[:8]
    __generate_experiment_directory(wdir=wdir, protocol=protocol, disable_pep=disable_pep,
                                    nodes_per_exp=nodes_per_exp, more_params=more_params, **kwargs)
    cmd = f'EXPDIR="{wdir}" HEPNOS_BUILD_PREFIX="{build_prefix}" {wdir}/job.sh &> "{wdir}.log"'
    print(f'Lauching {cmd}')
    os.system(cmd)
    dataloader_output_file = wdir + '/dataloader-output.txt'
    pep_output_file = wdir + '/pep-output.txt'
    dataloader_time = 99999999.0
    pep_time = 99999999.0
    result = 0.0
    try:
        for line in open(dataloader_output_file):
            if line.startswith('TIME'):
                dataloader_time = float(line.split()[1])
                break
        if dataloader_time >= 88888888.0:
            result = dataloader_time
        elif disable_pep:
            result = dataloader_time
        else:
            for line in open(pep_output_file):
                if 'Benchmark completed' in line:
                    pep_time = float(line.split()[-2])
            if pep_time >= 88888888.0:
                result = pep_time
            else:
                result = dataloader_time + pep_time
    except FileNotFoundError:
        result = 77777777.0
    rmtree(wdir)
    return -result


def build_deephyper_problem(disable_pep, more_params):
    """Generate a returns a DeepHyper problem."""
    from deephyper.problem import HpProblem
    problem = HpProblem()
    __fill_context(problem, __add_parameter_to_problem, disable_pep, more_params)
    return problem


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate an experiment')
    parser.add_argument('--wdir', required=True, type=str,
                        help='Directory in which to generate the configuration')
    default_protocol = os.environ.get('HEPNOS_LIBFABRIC_PROTOCOL','ofi+tcp')
    parser.add_argument('--protocol', default=default_protocol, type=str,
                        help='Mercury protocol to use')
    parser.add_argument('--hepnos_nodelist', required=False, default='', type=str,
                        help='Comma-separated list of nodes to use for HEPnOS')
    parser.add_argument('--loader_nodelist', required=False, default='', type=str,
                        help='Comma-separated list of nodes to use for the Dataloader')
    parser.add_argument('--pep_nodelist', required=False, default='', type=str,
                        help='Comma-separated list of nodes to use for Parallel Event Processor')
    parser.add_argument('--nodes_per_exp', required=False, default=4, type=int,
                        help='Number of nodes per workflow instance')
    parser.add_argument('--disable_pep', action='store_true',
                        help='Disable the PEP step in the workflow')
    parser.add_argument('--more_params', action='store_true',
                        help='Add 3 more parameters to the search space')
    __fill_context(parser, __add_parameter_to_parser)
    args = parser.parse_args()
    __generate_experiment_directory(**vars(args))
