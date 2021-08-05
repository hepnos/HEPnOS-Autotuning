import os, uuid
import yaml
from shutil import copyfile
import numpy as np
import time 

def __setup_directory():
    exp_dir = 'exp-' + str(uuid.uuid4())[0:8]
    os.mkdir(exp_dir)
    cwd = os.getcwd()
    return cwd + '/' + exp_dir

def __create_settings(exp_dir, loader_batch_size, loader_progress_thread,
                      pep_num_threads, pep_ibatch_size, pep_obatch_size,
                      pep_pes_per_node, pep_cores_per_pe):
#     settings_sh_in = os.path.dirname(os.path.abspath(__file__)) + '/scripts/settings.sh.in'
    settings_sh_in = '/lus/theta-fs0/projects/OptADDN/hepnos/github/HEPnOS-Autotuning/theta/scripts/settings.sh.in'
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
    hepnos_num_threads = args['num_threads'] # args[0] x1 
    hepnos_num_databases = args['num_databases'] # args[1] x2
    busy_spin = args['busy_spin'] # args[2] x3 
    loader_progress_thread = args['progress_thread'] # args[3] x4
    loader_batch_size = args['batch_size'] # args[4] x5 
#     pep_num_threads = args['num_threads_b'] #args[5] x6
    pep_cores_per_pe = int(max(1,int(args['pep_cores_per_pe']*64/float(args['pep_pes_per_node']))))  #args[9] x10
    pep_num_threads = min(31, int(1+(args['num_threads_b']*0.5*(pep_cores_per_pe-1)))) #args[5] x6 int(1+(x6_0*0.5*(x10-1))
    pep_ibatch_size = args['batch_size_in'] #args[6] x7 
    pep_obatch_size = args['batch_size_out'] #args[7]  x8 
    pep_pes_per_node = args['pep_pes_per_node'] #args[8] x9 
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
#     submit_sh = os.path.dirname(os.path.abspath(__file__)) + '/scripts/submit.sh'
    submit_sh ='/lus/theta-fs0/projects/OptADDN/hepnos/github/HEPnOS-Autotuning/theta/scripts/submit.sh'
    os.system(submit_sh + ' ' + exp_dir)
    print('Parsing result')
    t = __parse_result(exp_dir)
    print('Done (loading time = %f, processing time = %f)' % (t[0], t[1]))
    return 1 / (t[0]+t[1])
'''
Number of threads used by each benchmark process (should be between 1 and 31)
Size of the batches read from HEPnOS (I would suggest between 8 and 1024, to start with)
Size of the batches exchanged by benchmark processes (same range)
x6<=x10 and x9*x10<= 64
x6_0 = [0,1]  # actual range [1,31] integer: the number of processing threads per benchmark process
x9 = [1,64]   # actual range [1,64] integer: the number of PE per node for the benchmark
x10_0 = [0,1] # actual range [1,64] integer: the number of cores per PE for the benchmark
x10 = max(1, int(x10_0*64/x9)) where x10 ranges in [1,64] and x9*x10 <= 64. 
x6 = min(31, int(1+(x6_0*0.5*(x10-1)))) where x6 ranges in [1,31] and x6 <= x10 


'''
if __name__ == '__main__':
#     run([ 31, 16, False, False, 1024 ])
    config = {
        'num_threads': 31,
        'num_databases': 1,
        'busy_spin': False,
        'progress_thread': False,
        'batch_size': 1024,
        'num_threads_b': 1.0,
        'batch_size_in': 32,
        'batch_size_out': 1024,
        'pep_pes_per_node': 2,
        'pep_cores_per_pe': 1.0
    }
    objective = run(config)
    print('objective: ', objective)
    print('real run time: ', 1 / objective)
#     import matplotlib.pyplot as plt
#     plt.plot(HISTORY['val_r2'])
#     plt.xlabel('Epochs')
#     plt.ylabel('Objective: $R^2$')
#     plt.grid()
#     plt.show()
