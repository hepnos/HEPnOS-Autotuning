import os, uuid
import yaml
from shutil import copyfile


def __setup_directory():
    exp_dir = 'exp-' + str(uuid.uuid4())[0:8]
    os.mkdir(exp_dir)
    os.chdir(exp_dir)


def __create_settings(batch_size, progress_thread):
    copyfile('../scripts/settings.sh.in', 'settings.sh')
    with open('settings.sh', 'a+') as f:
        f.write('\n')
        if progress_thread:
            f.write('HEPNOS_CLIENT_USE_PROGRESS_THREAD=-a\n')
        else:
            f.write('HEPNOS_CLIENT_USE_PROGRESS_THREAD=\n')
        f.write('HEPNOS_CLIENT_BATCH_SIZE=%d\n' % batch_size)


def __generate_config_file(
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
    with open(filename, 'w+') as f:
        f.write(yaml.dump(config))


def __parse_result():
    for line in open('output.txt'):
        if 'real' in line:
            line = line.replace('s','')
            x = line.split()[1]
            m = int(x.split('m')[0])
            s = float(x.split('m')[1])
            return m*60 + s

def run(args):
    if len(args) != 5:
        raise RuntimeError("Expected 5 arguments in list, found %d" % len(args))
    num_threads = args[0]
    num_databases = args[1]
    busy_spin = args[2]
    progress_thread = args[3]
    batch_size = args[4]
    print('Setting up experiment\'s directory')
    __setup_directory()
    print('Creating settings.sh')
    __create_settings(batch_size, progress_thread)
    print('Creating config.yaml')
    __generate_config_file(
            threads=num_threads,
            busy_spin=busy_spin,
            targets=num_databases)
    print('Submitting job')
    os.system('../scripts/submit.sh')
    print('Parsing result')
    t = __parse_result()
    print('Done (result = %f)' % t)
    return t

if __name__ == '__main__':
    run([ 31, 16, False, False, 1024 ])
