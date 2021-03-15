import os, uuid
import yaml
from shutil import copyfile


def __setup_directory():
    exp_dir = 'exp-' + str(uuid.uuid4())[0:8]
    os.mkdir(exp_dir)
    cwd = os.getcwd()
    return cwd + '/' + exp_dir


def __create_settings(exp_dir, loader_batch_size, loader_progress_thread,
                      pep_num_threads, pep_ibatch_size, pep_obatch_size,
                      pep_pes_per_node, pep_cores_per_pe):
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
        if None not in [pep_num_threads, pep_ibatch_size, pep_obatch_size]:
            f.write('HEPNOS_ENABLE_PEP=1\n')
            f.write('HEPNOS_PEP_THREADS=%d\n' % pep_num_threads)
            f.write('HEPNOS_PEP_IBATCH_SIZE=%d\n' % pep_ibatch_size)
            f.write('HEPNOS_PEP_OBATCH_SIZE=%d\n' % pep_obatch_size)
            f.write('HEPNOS_PEP_PES_PER_NODE=%d\n' % pep_pes_per_node)
            f.write('HEPNOS_PEP_CORES_PER_PE=%d\n' % pep_cores_per_pe)
        else:
            f.write('HEPNOS_ENABLE_PEP=0\n')


def __generate_config_file(
        exp_dir='.',
        filename='config.yaml',
        threads=0,
        busy_spin=False,
        targets=1):
    config = dict()
    config['address'] = 'ofi+gni://'
    config['threads'] = int(threads)
    config['busy-spin'] = bool(busy_spin)
    config['databases'] = dict()
    config['databases']['datasets'] = dict()
    for k in ['datasets', 'runs', 'subruns', 'events', 'products']:
        config['databases'][k] = dict()
        d = config['databases'][k]
        d['name'] = 'hepnos-%s.$RANK.$PROVIDER.$TARGET' % k
        d['path'] = '/dev/shm/$RANK'
        d['type'] = 'map'
        d['targets'] = 1
        d['providers'] = 1
    config['databases']['events']['targets'] = int(targets)
    config['databases']['products']['targets'] = int(targets)
    with open(exp_dir+'/'+filename, 'w+') as f:
        f.write(yaml.dump(config))


def __parse_result(exp_dir):
    dataloader_time = 0
    pep_time = 0
    for line in open(exp_dir+'/dataloader-output.txt'):
        if 'real' in line:
            line = line.replace('s','')
            x = line.split()[1]
            m = int(x.split('m')[0])
            s = float(x.split('m')[1])
            dataloader_time = m*60 + s
    if os.path.isfile(exp_dir+'/pep-output.txt'):
        for line in open(exp_dir+'/pep-output.txt'):
            if 'real' in line:
                line = line.replace('s','')
                x = line.split()[1]
                m = int(x.split('m')[0])
                s = float(x.split('m')[1])
                pep_time = m*60 + s
    return (dataloader_time, pep_time)


def run(args):
    if len(args) == 5:
        args.extend([None, None, None, None, None])
    if len(args) == 8:
        args.extend([2, 32])
    if len(args) != 10:
        raise RuntimeError("Expected 5 or 10 arguments in list, found %d" % len(args))
    hepnos_num_threads = args[0]
    hepnos_num_databases = args[1]
    busy_spin = args[2]
    loader_progress_thread = args[3]
    loader_batch_size = args[4]
    pep_num_threads = args[5]
    pep_ibatch_size = args[6]
    pep_obatch_size = args[7]
    pep_pes_per_node = args[8]
    pep_cores_per_pe = args[9]
    print('Setting up experiment\'s directory')
    exp_dir = __setup_directory()
    print('Creating settings.sh')
    __create_settings(exp_dir,
                      loader_batch_size,
                      loader_progress_thread,
                      pep_num_threads,
                      pep_ibatch_size,
                      pep_obatch_size,
                      pep_pes_per_node,
                      pep_cores_per_pe)
    print('Creating config.yaml')
    __generate_config_file(
            exp_dir,
            threads=hepnos_num_threads,
            busy_spin=busy_spin,
            targets=hepnos_num_databases)
    print('Submitting job')
    submit_sh = os.path.dirname(os.path.abspath(__file__)) + '/scripts/submit.sh'
    os.system(submit_sh + ' ' + exp_dir)
    print('Parsing result')
    t = __parse_result(exp_dir)
    print('Done (loading time = %f, processing time = %f)' % (t[0], t[1]))
    return t[0]+t[1]

if __name__ == '__main__':
    # The format of the argument array is is:
    # - number of RPC handling threads per process for HEPnOS
    # - number of databases per process for HEPnOS
    # - whether to use busy spinning or not
    # - whether to use a progress thread or not in clients
    # - the batch size for the dataloader
    # If you want to run the PEP benchmark as well,
    # the following parameters must be added:
    # - number of processing threads per benchmark process (must be > 0)
    # - batch size when loading from HEPnOS
    # - batch size when loading from another rank
    # If you want to configure the number of PES and cores per PE for
    # the benchmark, you can add two more parameters:
    # - number of PES per node (must be between 1 and 64)
    # - number of cores per PE (must be between 1 and 64)
    # The product of the these two parameters should not exceed 64.
    # Additionally, the number of processing threads should be
    # the number of cores per PE minus 2 (so effectively the number
    # cores per PE must be at least 3).
    run([ 31, 1, False, False, 1024, 31, 32, 1024, 2, 32 ])
    #run([ 31, 1, False, False, 1024 ])
