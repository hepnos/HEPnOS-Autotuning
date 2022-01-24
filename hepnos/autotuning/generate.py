import sys
import os
import argparse
import mochi.bedrock.spec as brk
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'




def __generate_hepnos_config(wdir, protocol, busy_spin,
                             hepnos_progress_thread,
                             hepnos_num_rpc_threads,
                             hepnos_num_event_databases,
                             hepnos_num_product_databases,
                             hepnos_num_providers,
                             hepnos_pool_type,
                             **kwargs):
    """Generate a JSON configuration for Bedrock to deploy HEPnOS."""
    proc_spec = brk.ProcSpec(margo=protocol)
    # Add yokan library
    proc_spec.libraries['yokan'] = 'libyokan-bedrock-module.so'
    # Setup busy-spinning if requested
    if busy_spin:
        proc.margo.mercury.na_no_block = True
    # Add SSG group
    proc_spec.ssg.add(name='hepnos', bootstrap='mpi', group_file='hepnos.ssg',
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
    for i in range(hepnos_num_providers):
        rpc_pool = proc_spec.margo.argobots.pools.add(
            name=f'__rpc_pool_{i}__', kind=hepnos_pool_type, access='mpmc')
        rpc_pools.append(rpc_pool)
    if hepnos_num_providers == 0:
        rpc_pools.append(proc_spec.margo.rpc_pool)
    # Setup additional xstreams
    for i in range(hepnos_num_rpc_threads):
        pools = []
        if hepnos_num_rpc_threads < hepnos_num_providers:
            j = i
            while j < len(rpc_pools):
                pools.append(f'__rpc_pool_{j}__')
                j += hepnos_num_rpc_threads
        else:
            pools = [f'__rpc_pool_{i % hepnos_num_providers}__']
        pools = [ proc_spec.margo.argobots.pools[p] for p in pools ]
        proc_spec.margo.argobots.xstreams.add(
            name=f'__rpc_es_{i}__', scheduler=brk.SchedulerSpec(pools=pools))
    if hepnos_num_rpc_threads == 0:
        pools = [f'__rpc_pool_{i}__' for i in range(hepnos_num_providers)]
        pools = [proc_spec.margo.argobots.pools[p] for p in pools]
        proc_spec.margo.argobots.xstreams[0].scheduler.pools = pools
    # Create databases
    dbs = []
    dbs.append({ "name": 'hepnos-datasets-0', "type": 'map', "config": {} })
    dbs.append({ "name": 'hepnos-runs-0', "type": 'set', "config": {} })
    dbs.append({ "name": 'hepnos-subruns-0', "type": 'set', "config": {} })
    for i in range(hepnos_num_event_databases):
        dbs.append({ "name": f'hepnos-events-{i}', "type": 'set', "config": {} })
    for i in range(hepnos_num_product_databases):
        dbs.append({ "name": f'hepnos-products-{i}', "type": 'set', "config": {} })
    # Setup providers
    providers = []
    for i in range(hepnos_num_providers):
        proc_spec.providers.add(name=f'hepnos_{i}',
                                type='yokan', pool=rpc_pools[i],
                                provider_id=i+1,
                                config={'databases': []})
    # Bind databases to providers
    for i, db in enumerate(dbs):
        proc_spec.providers[i%hepnos_num_providers].config['databases'].append(db)
    # Generate configuration
    with open(f'{wdir}/hepnos.json', 'w+') as config:
        config.write(proc_spec.to_json(indent=4))


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


def __fill_context(context, add_parameter):
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
    add_parameter(context, "hepnos_pool_type", str, 'fifo_wait', ['fifo','fifo_wait','prio_wait'],
        "Thread-scheduling policity used by Argobots pools")
    add_parameter(context, "hepnos_pes_per_node", int, 2, [1, 2, 4, 8, 16, 32],
        "Number of HEPnOS processes per node")
    add_parameter(context, "loader_progress_thread", bool, True, [True, False],
        "Whether to use a dedicated progress thread in the Dataloader")
    add_parameter(context, "loader_batch_size", int, 512, (1, 2048, "log-uniform"),
        "Size of the batches of events sent by the Dataloader to HEPnOS")
    add_parameter(context, "loader_pes_per_node", int, 2, [1, 2, 4, 8, 16],
        "Number of processes per node for the Dataloader")
    add_parameter(context, "loader_async", bool, False, [True, False],
        "Whether to use the HEPnOS AsyncEngine in the Dataloader")
    add_parameter(context, "loader_async_threads", int, 1, (1, 63, "log-uniform"),
        "Number of threads for the AsyncEngine to use")
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
    add_parameter(context, "pep_use_preloading", bool, True, [True, False],
        "Whether the PEP step should use product-preloading")


def generate_experiment_directory(wdir, **kwargs):
    os.mkdir(wdir)
    __generate_hepnos_config(wdir=wdir, **kwargs)


def generate_deephyper_problem():
    """Generate a returns a DeepHyper problem."""
    from deephyper.problem import HpProblem
    problem = HpProblem()
    __fill_context(problem, __add_parameter_to_problem)
    return problem


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate an experiment')
    parser.add_argument('--wdir', required=True, type=str,
                        help='Directory in which to generate the configuration')
    parser.add_argument('--protocol', required=True, type=str,
                        help='Mercury protocol to use')
    __fill_context(parser, __add_parameter_to_parser)
    args = parser.parse_args()
    generate_experiment_directory(**vars(args))