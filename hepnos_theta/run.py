import os, uuid
import copy
import json
import re
from shutil import copyfile


def __setup_directory():
    exp_dir = 'exp-' + str(uuid.uuid4())[0:8]
    os.mkdir(exp_dir)
    cwd = os.getcwd()
    return cwd + '/' + exp_dir


def __make_node_list(nodes):
    if nodes is None:
        return None
    result = []
    for n in nodes:
        m = re.search('([0-9]+)', n)
        result.append(str(int(str(m.group(0)))))
    return result


def __create_settings(exp_dir, loader_batch_size, loader_progress_thread, enable_pep,
                      pep_num_threads, pep_ibatch_size, pep_obatch_size, pep_use_preloading,
                      pep_pes_per_node, pep_cores_per_pe, nodes):
    settings_sh_in = os.path.dirname(os.path.abspath(__file__)) + '/scripts/settings.sh.in'
    settings_sh = exp_dir + '/settings.sh'
    copyfile(settings_sh_in, settings_sh)
    with open(settings_sh, 'a+') as f:
        f.write('\n')
        if loader_progress_thread:
            f.write('HEPNOS_LOADER_CLIENT_USE_PROGRESS_THREAD=-a\n')
        else:
            f.write('HEPNOS_LOADER_CLIENT_USE_PROGRESS_THREAD=\n')
        f.write('HEPNOS_LOADER_CLIENT_BATCH_SIZE=%d\n' % loader_batch_size)
        if enable_pep:
            f.write('HEPNOS_ENABLE_PEP=1\n')
            f.write('HEPNOS_PEP_THREADS=%d\n' % pep_num_threads)
            f.write('HEPNOS_PEP_IBATCH_SIZE=%d\n' % pep_ibatch_size)
            f.write('HEPNOS_PEP_OBATCH_SIZE=%d\n' % pep_obatch_size)
            f.write('HEPNOS_PEP_PES_PER_NODE=%d\n' % pep_pes_per_node)
            f.write('HEPNOS_PEP_CORES_PER_PE=%d\n' % pep_cores_per_pe)
            if pep_use_preloading:
                f.write('HEPNOS_PEP_PRELOAD=--preload\n')
            else:
                f.write('HEPNOS_PEP_PRELOAD=\n')
        else:
            f.write('HEPNOS_ENABLE_PEP=0\n')
        if nodes is not None:
            f.write('HEPNOS_NODELIST=(%s)\n' % ' '.join(nodes))


def __generate_client_config_file(
        exp_dir='.',
        filename='client.json',
        busy_spin=False):
    client_json_in = os.path.dirname(os.path.abspath(__file__)) + '/scripts/client.json.in'
    client_json = exp_dir + '/' + filename
    with open(client_json_in) as f:
        config = json.loads(f.read())
    config['mercury']['na_no_block'] = bool(busy_spin)
    with open(client_json, 'w+') as f:
        f.write(json.dumps(config))


def __generate_hepnos_config_file(
        exp_dir='.',
        filename='hepnos.json',
        threads=0,
        busy_spin=False,
        targets=1):
    hepnos_json_in = os.path.dirname(os.path.abspath(__file__)) + '/scripts/hepnos.json.in'
    hepnos_json = exp_dir + '/' + filename
    with open(hepnos_json_in) as f:
        config = json.loads(f.read())

    config['margo']['rpc_thread_count'] = int(threads)
    config['margo']['mercury']['na_no_block'] = bool(busy_spin)
    ssg_group = None
    for g in config['ssg']:
        if g['name'] == 'hepnos':
            ssg_group = g
            break
    ssg_group['group_file'] = exp_dir + '/hepnos.ssg'

    event_db_model = {
            "type" : "map",
            "comparator" : "hepnos_compare_item_descriptors",
            "no_overwrite" : True
    }
    product_db_model = {
            "type" : "map",
            "no_overwrite" : True
    }

    hepnos_provider = None
    for p in config['providers']:
        if p['name'] == 'hepnos':
            hepnos_provider = p
            break

    for i in range(0, targets):
        event_db_name = 'hepnos-events-' + str(i)
        product_db_name = 'hepnos-products-' + str(i)
        event_db = copy.deepcopy(event_db_model)
        event_db['name'] = event_db_name
        product_db = copy.deepcopy(product_db_model)
        product_db['name'] = product_db_name
        hepnos_provider['config']['databases'].append(event_db)
        hepnos_provider['config']['databases'].append(product_db)

    with open(hepnos_json, 'w+') as f:
        f.write(json.dumps(config))


def __parse_result(exp_dir):
    dataloader_time = 99999999
    pep_time = 0
    if os.path.isfile(exp_dir+'/dataloader-output.txt'):
        for line in open(exp_dir+'/dataloader-output.txt'):
            if 'ESTIMATED' in line:
                dataloader_time = int(float(line.split()[-1]))
                break
            if 'RUNTIME' in line:
                dataloader_time = int(float(line.split()[-1]))
                break
    if os.path.isfile(exp_dir+'/pep-output.txt'):
        pep_time = 99999999
        for line in open(exp_dir+'/pep-output.txt'):
            if 'TIME:' in line:
                pep_time = int(line.split()[1])
    return (dataloader_time, pep_time)


def run(config, nodes=None):

    # collect hyperparameter
    hepnos_num_threads = config["hepnos_num_threads"]
    hepnos_num_databases = config["hepnos_num_databases"]
    busy_spin = config["busy_spin"]
    loader_progress_thread = config["loader_progress_thread"]
    loader_batch_size = config["loader_batch_size"]

    enable_pep = bool(int(os.environ.get("DH_HEPNOS_ENABLE_PEP", 0)))
    pep_num_threads = config.get("pep_num_threads", None)
    pep_ibatch_size = config.get("pep_ibatch_size", None)
    pep_obatch_size = config.get("pep_obatch_size", None)
    pep_use_preloading = config.get("pep_use_preloading", None)
    pep_pes_per_node = config.get("pep_pes_per_node", None)
    pep_cores_per_pe = config.get("pep_cores_per_pe", None)

    nodes = __make_node_list(nodes)
    print('Setting up experiment\'s directory')
    exp_dir = __setup_directory()
    print('Creating settings.sh')
    __create_settings(exp_dir,
                      loader_batch_size,
                      loader_progress_thread,
                      enable_pep,
                      pep_num_threads,
                      pep_ibatch_size,
                      pep_obatch_size,
                      pep_use_preloading,
                      pep_pes_per_node,
                      pep_cores_per_pe,
                      nodes)
    print('Creating hepnos.json')
    __generate_hepnos_config_file(
            exp_dir,
            threads=hepnos_num_threads,
            busy_spin=busy_spin,
            targets=hepnos_num_databases)
    print('Creating client.json')
    __generate_client_config_file(
            exp_dir,
            busy_spin=busy_spin)
    print('Submitting job')
    submit_sh = os.path.dirname(os.path.abspath(__file__)) + '/scripts/submit.sh'
    os.system(submit_sh + ' ' + exp_dir)
    print('Parsing result')
    t = __parse_result(exp_dir)
    print('Done (loading time = %f, processing time = %f)' % (t[0], t[1]))
    return -(t[0]+t[1])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='HEPnOS experiment')
    parser.add_argument('--hepnos-num-threads', type=int, default=31,
                        help='number of RPC handling threads per process for HEPnOS')
    parser.add_argument('--hepnos-num-databases', type=int, default=1,
                        help='number of databases per process for HEPnOS')
    parser.add_argument('--busy-spin', action='store_true', default=False,
                        help='whether to use busy spinning or not')
    parser.add_argument('--loader-progress-thread', action='store_true', default=False,
                        help='whether to use a progress thread or not in dataloader clients')
    parser.add_argument('--loader-batch-size', type=int, default=1024,
                        help='batch size for the dataloader')
    parser.add_argument('--enable-pep', action='store_true', default=False,
                        help='enable PEP benchmark')
    parser.add_argument('--pep-num-threads', type=int, default=31,
                        help='number of processing threads per benchmark process (must be > 0)')
    parser.add_argument('--pep-ibatch-size', type=int, default=32,
                        help='batch size when loading from HEPnOS')
    parser.add_argument('--pep-obatch-size', type=int, default=32,
                        help='batch size when loading from another rank')
    parser.add_argument('--pep-use-preloading', action='store_true', default=False,
                        help='whether to use product-preloading')
    parser.add_argument('--pep-pes-per-node', type=int, default=16,
                        help='number of PES per node (must be between 1 and 64)')
    parser.add_argument('--pep-cores-per-pe', type=int, default=4,
                        help='number of cores per PE (must be between 1 and 64)')
    parser.add_argument('--nodes', type=str, default=None,
                        help='nodes to use')
    # The product of the last wo parameters should not exceed 64.
    # Additionally, the number of processing threads should be
    # the number of cores per PE minus 2 (so effectively the number
    # cores per PE must be at least 3).
    ns = parser.parse_args()
    if ns.nodes is not None:
        ns.nodes = ns.nodes.split(',')
    run(vars(ns))
