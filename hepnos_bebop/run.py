import os, uuid
import copy
import json
import re
from shutil import copyfile


def __setup_directory(id_=None):
    if id_ == None:
        id_ = uuid.uuid4()
    exp_dir = 'exp-' + str(id_)
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


def __create_settings(exp_dir, hepnos_pes_per_node, loader_batch_size,
                      loader_async, loader_async_threads, loader_pes_per_node,
                      enable_pep, pep_num_threads, pep_ibatch_size,
                      pep_obatch_size, pep_use_preloading, pep_pes_per_node,
                      nodes):
    settings_sh_in = os.path.dirname(
        os.path.abspath(__file__)) + '/scripts/settings.sh.in'
    settings_sh = exp_dir + '/settings.sh'
    copyfile(settings_sh_in, settings_sh)
    with open(settings_sh, 'a+') as f:
        f.write('\n')
        f.write('HEPNOS_PES_PER_NODE=%d\n' % hepnos_pes_per_node)
        if loader_async:
            f.write('HEPNOS_LOADER_ASYNC=-a\n')
            f.write('HEPNOS_LOADER_ASYNC_THREADS=%d\n' % loader_async_threads)
        else:
            f.write('HEPNOS_LOADER_ASYNC=\n')
            f.write('HEPNOS_LOADER_ASYNC_THREADS=0\n')
        f.write('HEPNOS_LOADER_BATCH_SIZE=%d\n' % loader_batch_size)
        f.write('HEPNOS_LOADER_PES_PER_NODE=%d\n' % loader_pes_per_node)
        if enable_pep:
            f.write('HEPNOS_ENABLE_PEP=1\n')
            f.write('HEPNOS_PEP_THREADS=%d\n' % pep_num_threads)
            f.write('HEPNOS_PEP_IBATCH_SIZE=%d\n' % pep_ibatch_size)
            f.write('HEPNOS_PEP_OBATCH_SIZE=%d\n' % pep_obatch_size)
            f.write('HEPNOS_PEP_PES_PER_NODE=%d\n' % pep_pes_per_node)
            if pep_use_preloading:
                f.write('HEPNOS_PEP_PRELOAD=--preload\n')
            else:
                f.write('HEPNOS_PEP_PRELOAD=\n')
        else:
            f.write('HEPNOS_ENABLE_PEP=0\n')
        if nodes is not None:
            f.write('HEPNOS_NODELIST=(%s)\n' % ' '.join(nodes))


def __generate_dataloader_config_file(exp_dir='.',
                                      filename='dataloader.json',
                                      busy_spin=False,
                                      use_progress_thread=False):
    dataloader_json_in = os.path.dirname(
        os.path.abspath(__file__)) + '/scripts/dataloader.json.in'
    dataloader_json = exp_dir + '/' + filename
    with open(dataloader_json_in) as f:
        config = json.loads(f.read())
    config['mercury']['na_no_block'] = bool(busy_spin)
    config['use_progress_thread'] = bool(use_progress_thread)
    with open(dataloader_json, 'w+') as f:
        f.write(json.dumps(config, indent=4))


def __generate_pep_config_file(exp_dir='.',
                               filename='pep.json',
                               busy_spin=False,
                               use_progress_thread=False):
    pep_json_in = os.path.dirname(
        os.path.abspath(__file__)) + '/scripts/pep.json.in'
    pep_json = exp_dir + '/' + filename
    with open(pep_json_in) as f:
        config = json.loads(f.read())
    config['mercury']['na_no_block'] = bool(busy_spin)
    config['use_progress_thread'] = bool(use_progress_thread)
    with open(pep_json, 'w+') as f:
        f.write(json.dumps(config, indent=4))


def __generate_hepnos_config_file(exp_dir='.',
                                  filename='hepnos.json',
                                  busy_spin=False,
                                  use_progress_thread=False,
                                  num_threads=0,
                                  num_providers=1,
                                  num_event_dbs=1,
                                  num_product_dbs=1,
                                  pool_type='fifo_wait'):
    hepnos_json_in = os.path.dirname(
        os.path.abspath(__file__)) + '/scripts/hepnos.json.in'
    hepnos_json = exp_dir + '/' + filename
    with open(hepnos_json_in) as f:
        config = json.loads(f.read())

    config['margo']['mercury']['na_no_block'] = bool(busy_spin)
    config['margo']['argobots']['pools'][0]['type'] = pool_type

    if use_progress_thread:
        config['margo']['argobots']['pools'].append({
            'name': '__progress__',
            'type': pool_type,
            'access': 'mpmc'
        })
        config['margo']['argobots']['xstreams'].append({
            'name': '__progress__',
            'scheduler': {
                'type': 'basic_wait',
                'pools': ['__progress__']
            }
        })
        config['margo']['progress_pool'] = '__progress__'
    else:
        config['margo']['progress_pool'] = '__primary__'

    rpc_pools = []
    for i in range(0, num_providers):
        config['margo']['argobots']['pools'].append({
            'name': ('__rpc_%d__' % i),
            'type': pool_type,
            'access': 'mpmc'
        })
        rpc_pools.append('__rpc_%d__' % i)

    if num_threads == 0:
        config['margo']['argobots']['xstreams'][0]['scheduler'][
            'pools'].extend(rpc_pools)
    else:
        es = []
        for i in range(0, min(num_threads, num_providers)):
            config['margo']['argobots']['xstreams'].append({
                'name': ('rpc_es_%d' % i),
                'scheduler': {
                    'type': 'basic_wait',
                    'pools': []
                }
            })
            es.append(config['margo']['argobots']['xstreams'][-1])
        for i in range(0, len(rpc_pools)):
            es[i % len(es)]['scheduler']['pools'].append(rpc_pools[i])

    ssg_group = None
    for g in config['ssg']:
        if g['name'] == 'hepnos':
            ssg_group = g
            break
    ssg_group['group_file'] = exp_dir + '/hepnos.ssg'

    event_db_model = {
        "type": "map",
        "comparator": "hepnos_compare_item_descriptors",
        "no_overwrite": True
    }
    product_db_model = {"type": "map", "no_overwrite": True}

    for i in range(0, num_providers):
        p = {
            "name": "hepnos_data_%d" % (i + 1),
            "type": "sdskv",
            "pool": rpc_pools[i % len(rpc_pools)],
            "provider_id": i + 1,
            "config": {
                "comparators": [{
                    "name": "hepnos_compare_item_descriptors",
                    "library": "libhepnos-service.so"
                }],
                "databases": []
            }
        }
        config['providers'].append(p)

    p = 0
    for i in range(0, num_event_dbs):
        event_db_name = 'hepnos-events-' + str(i)
        event_db = copy.deepcopy(event_db_model)
        event_db['name'] = event_db_name
        provider = config['providers'][1 + (p %
                                            (len(config['providers']) - 1))]
        provider['config']['databases'].append(event_db)
        p += 1

    for i in range(0, num_product_dbs):
        product_db_name = 'hepnos-products-' + str(i)
        product_db = copy.deepcopy(product_db_model)
        product_db['name'] = product_db_name
        provider = config['providers'][1 + (p %
                                            (len(config['providers']) - 1))]
        provider['config']['databases'].append(product_db)
        p += 1

    with open(hepnos_json, 'w+') as f:
        f.write(json.dumps(config, indent=4))


def __parse_result(exp_dir):
    dataloader_time = 99999999
    pep_time = 0
    if os.path.isfile(exp_dir + '/dataloader-output.txt'):
        for line in open(exp_dir + '/dataloader-output.txt'):
            if 'ESTIMATED' in line:
                dataloader_time = int(float(line.split()[-1]))
                break
            if 'RUNTIME' in line:
                dataloader_time = int(float(line.split()[-1]))
                break
    if os.path.isfile(exp_dir + '/pep-output.txt'):
        pep_time = 99999999
        for line in open(exp_dir + '/pep-output.txt'):
            if 'TIME:' in line:
                pep_time = int(line.split()[1])
    return (dataloader_time, pep_time)


def run(config, nodes=None):

    enable_pep = config.get('enable_pep',
                            int(os.environ.get("DH_HEPNOS_EXP_STEP", 1)) >= 2)

    hepnos_pes_per_node = config.get("hepnos_pes_per_node", 2)
    hepnos_progress_thread = config.get("hepnos_progress_thread", False)
    hepnos_num_threads = config.get("hepnos_num_threads", 31)
    hepnos_num_event_databases = config.get("hepnos_num_event_databases", 1)
    hepnos_num_product_databases = config.get("hepnos_num_product_databases",
                                              1)
    hepnos_pool_type = config.get("hepnos_pool_type", "fifo_wait")
    hepnos_num_providers = config.get("hepnos_num_providers", 1)
    busy_spin = config.get("busy_spin", False)

    loader_progress_thread = config.get("loader_progress_thread", False)
    loader_async = config.get("loader_async", False)
    loader_async_threads = config.get("loader_async_threads", 1)
    loader_batch_size = config.get("loader_batch_size", 1024)
    loader_pes_per_node = config.get("loader_pes_per_node", 1)

    pep_progress_thread = config.get("pep_progress_thread", False)
    pep_num_threads = config.get("pep_num_threads", 31)
    pep_ibatch_size = config.get("pep_ibatch_size", 32)
    pep_obatch_size = config.get("pep_obatch_size", 32)
    pep_use_preloading = config.get("pep_use_preloading", False)
    pep_pes_per_node = config.get("pep_pes_per_node", 16)

#    print('Using nodes '+str(nodes))
#    nodes = __make_node_list(nodes)
#    print('Using nodes '+str(nodes))
    print('Setting up experiment\'s directory')
    exp_dir = __setup_directory(config.get("id"))
    print('Creating settings.sh')
    __create_settings(exp_dir, hepnos_pes_per_node, loader_batch_size,
                      loader_async, loader_async_threads, loader_pes_per_node,
                      enable_pep, pep_num_threads, pep_ibatch_size,
                      pep_obatch_size, pep_use_preloading, pep_pes_per_node,
                      nodes)
    print('Creating hepnos.json')
    __generate_hepnos_config_file(exp_dir,
                                  busy_spin=busy_spin,
                                  use_progress_thread=hepnos_progress_thread,
                                  num_threads=hepnos_num_threads,
                                  num_providers=hepnos_num_providers,
                                  num_event_dbs=hepnos_num_event_databases,
                                  num_product_dbs=hepnos_num_product_databases,
                                  pool_type=hepnos_pool_type)
    print('Creating dataloader.json')
    __generate_dataloader_config_file(
        exp_dir,
        busy_spin=busy_spin,
        use_progress_thread=loader_progress_thread)
    if enable_pep:
        print('Creating pep.json')
        __generate_pep_config_file(exp_dir,
                                   busy_spin=busy_spin,
                                   use_progress_thread=pep_progress_thread)
    print('Submitting job')
    submit_sh = os.path.dirname(
        os.path.abspath(__file__)) + '/scripts/submit.sh'
    os.system(submit_sh + ' ' + exp_dir)
    print('Parsing result')
    t = __parse_result(exp_dir)
    print('Done (loading time = %f, processing time = %f)' % (t[0], t[1]))
    return -(t[0] + t[1])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='HEPnOS experiment')

    parser.add_argument('--hepnos-pes-per-node',
                        type=int,
                        default=2,
                        help='number of PE per node for HEPnOS')
    parser.add_argument('--hepnos-progress-thread',
                        action='store_true',
                        default=False,
                        help='whether to use a progress thread in HEPnOS')
    parser.add_argument(
        '--hepnos-num-threads',
        type=int,
        default=31,
        help='number of RPC handling threads per process for HEPnOS')
    parser.add_argument(
        '--hepnos-num-providers',
        type=int,
        default=1,
        help='number of providers managing databases in HEPnOS')
    parser.add_argument(
        '--hepnos-num-event-databases',
        type=int,
        default=1,
        help='number of databases per process for events in HEPnOS')
    parser.add_argument(
        '--hepnos-num-product-databases',
        type=int,
        default=1,
        help='number of databases per process for products in HEPnOS')
    # pool type can be "fifo", "fifo_wait", or "prio_wait"
    parser.add_argument('--hepnos-pool-type',
                        type=str,
                        default='fifo_wait',
                        help='type of Argobots pools to use in HEPnOS')
    parser.add_argument('--busy-spin',
                        action='store_true',
                        default=False,
                        help='whether to use busy spinning or not')

    parser.add_argument(
        '--loader-progress-thread',
        action='store_true',
        default=False,
        help='whether to use a progress thread or not in dataloader clients')
    parser.add_argument(
        '--loader-async',
        action='store_true',
        default=False,
        help='whether to use async progress in dataloader clients')
    parser.add_argument(
        '--loader-async-threads',
        type=int,
        default=1,
        help='number of threads for async operation in clients')
    parser.add_argument('--loader-batch-size',
                        type=int,
                        default=1024,
                        help='batch size for the dataloader')
    parser.add_argument(
        '--loader-pes-per-node',
        type=int,
        default=1,
        help='number of PES per node (must be between 1 and 64) for loader')

    parser.add_argument('--enable-pep',
                        action='store_true',
                        default=False,
                        help='enable PEP benchmark')

    parser.add_argument('--pep-progress-thread',
                        action='store_true',
                        default=False,
                        help='whether to use a progress thread or not in PEP')
    parser.add_argument(
        '--pep-num-threads',
        type=int,
        default=31,
        help='number of processing threads per benchmark process (must be > 0)'
    )
    parser.add_argument('--pep-ibatch-size',
                        type=int,
                        default=32,
                        help='batch size when loading from HEPnOS')
    parser.add_argument('--pep-obatch-size',
                        type=int,
                        default=32,
                        help='batch size when loading from another rank')
    parser.add_argument('--pep-use-preloading',
                        action='store_true',
                        default=False,
                        help='whether to use product-preloading')
    parser.add_argument(
        '--pep-pes-per-node',
        type=int,
        default=16,
        help='number of PES per node (must be between 1 and 64)')
    parser.add_argument(
        '--pep-cores-per-pe',
        type=int,
        default=-1,
        help='number of cores per PE (must be between 1 and 64)')

    parser.add_argument('--nodes', type=str, default=None, help='nodes to use')
    # The product of the last wo parameters should not exceed 64.
    # Additionally, the number of processing threads should be
    # the number of cores per PE minus 2 (so effectively the number
    # cores per PE must be at least 3).
    ns = parser.parse_args()
    if ns.nodes is not None:
        ns.nodes = ns.nodes.split(',')
    run(vars(ns), ns.nodes)
