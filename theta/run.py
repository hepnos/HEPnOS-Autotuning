import os, uuid
import yaml
from shutil import copyfile


def __setup_directory():
    exp_dir = 'exp-' + str(uuid.uuid4())[0:8]
    os.mkdir(exp_dir)
    cwd = os.getcwd()
    return cwd + '/' + exp_dir


def __create_settings(exp_dir, batch_size, progress_thread):
    settings_sh_in = os.path.dirname(os.path.abspath(__file__)) + '/scripts/settings.sh.in'
    settings_sh = exp_dir + '/settings.sh'
    copyfile(settings_sh_in, settings_sh)
    with open(settings_sh, 'a+') as f:
        f.write('\n')
        if progress_thread:
            f.write('HEPNOS_CLIENT_USE_PROGRESS_THREAD=-a\n')
        else:
            f.write('HEPNOS_CLIENT_USE_PROGRESS_THREAD=\n')
        f.write('HEPNOS_CLIENT_BATCH_SIZE=%d\n' % batch_size)


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
    for line in open(exp_dir+'/output.txt'):
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
    exp_dir = __setup_directory()
    print('Creating settings.sh')
    __create_settings(exp_dir, batch_size, progress_thread)
    print('Creating config.yaml')
    __generate_config_file(
            exp_dir,
            threads=num_threads,
            busy_spin=busy_spin,
            targets=num_databases)
    print('Submitting job')
    submit_sh = os.path.dirname(os.path.abspath(__file__)) + '/scripts/submit.sh'
    os.system(submit_sh + ' ' + exp_dir)
    print('Parsing result')
    t = __parse_result(exp_dir)
    print('Done (result = %f)' % t)
    return t

if __name__ == '__main__':
    run([ 31, 3, False, False, 1024 ])
