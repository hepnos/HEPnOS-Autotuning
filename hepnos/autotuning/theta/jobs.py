import logging
import sys
import os
import subprocess


def generate_header(A, t, n, q, **kwargs):
    """Generates the header of the job script."""
    if len(q) == 0:
        q = 'default' if n >= 128 else 'debug-flat-quad'
    preamble = '#!/usr/bin/env bash\n'
    if len(A) != 0:
        preamble += f'#COBALT -A {A}\n'
    preamble += f'#COBALT -t {t}\n'
    preamble += f'#COBALT -n {n}\n'
    preamble += f'#COBALT -q {q}\n'
    return preamble


def generate_prologue(**kwargs):
    """Generates the prologue for the job."""
    prologue = ''
    if 'pdomain' in kwargs:
        pdomain = kwargs['pdomain']
        prologue += f'apstat -P | grep {pdomain} || apmgr pdomain -c -u {pdomain}'
    return prologue


def generate_epilogue(**kwargs):
    """Generate the epilogue for the job."""
    epilogue = ''
    if 'pdomain' in kwargs:
        pdomain = kwargs['pdomain']
        epilogue += 'echo "Destroying protection domain"'
        epilogue += f'apmgr pdomain -r -u {pdomain}'
    return epilogue


def generate_mpirun(program, num_nodes, pes_per_node, **kwargs):
    """Generate an mpirun command for the platform."""
    num_pes = num_nodes*pes_per_node
    cmd = f'aprun -n {num_pes} -N {pes_per_node} '
    if 'node_list' in kwargs:
        node_list = kwargs['node_list']
        if isinstance(node_list, list):
            nodes = ','.join(node_list)
            cmd += f'-L {nodes} '
        else:
            cmd += f'-L {node_list} '
    if 'pdomain' in kwargs:
        pdomain = kwargs['pdomain']
        cmd += f'-p {pdomain} '
    cmd += program
    return cmd


def __parse_header_from_script(filename):
    interpreter_dir = False
    result = dict()
    flag_translation = {
        '-A': 'allocation',
        '--allocation': 'allocation',
        '-t': 'time',
        '--time': 'time',
        '-n': 'nodes',
        '--nodes': 'nodes',
        '-q': 'queue',
        '--queue': 'queue',
        '-p': 'partition',
        '--partition': 'partition'
    }
    for line in open(filename):
        _conditions = []
        if line.startswith('#!'):
            if interpreter_dir:
                return args
            else:
                interpreter_dir = True
            continue
        elif line.startswith('#H '):
            elems = line.split()[1:]
            if len(elems) == 0:
                raise ValueError(f'Invalid header line {line}')
            flag = elems[0]
            value = elems[1]
            if flag in flag_translation:
                result[flag_translation[flag]] = value
        else:
            break
    return result


def submit(command, **kwargs):
    cmd = ['qsub']
    args = kwargs
    if len(command) == 0:
        logging.critical("No command provided")
        sys.exit(-1)
    header_args = __parse_header_from_script(command[0])
    for k, v in header_args.items():
        if k in args and args[k] is None:
            args[k] = header_args[k]
    if args['allocation'] is not None:
        cmd += [f'-A {args["allocation"]}']
    if args['time'] is not None:
        cmd += [f'-t {args["time"]}']
    if args['nodes'] is not None:
        cmd += [f'-n {args["nodes"]}']
    if args['queue'] is not None:
        cmd += [f'-q {args["queue"]}']
    extra = args['extra']
    if extra.startswith('"') and extra.endswith('"'):
        extra = extra[1:-1]
    if extra.startswith("'") and extra.endswith("'"):
        extra = extra[1:-1]
    extra = extra.split(',')
    cmd += extra
    cmd += command
    cmd = ' '.join(cmd)
    os.system(cmd)


def __output_forwarder(pipe, out):
    try:
        with pipe:
            for line in iter(pipe.readline, b''):
                out.write(line.decode())
                out.flush()
    finally:
        pass


def __run_command_in_subprocess(cmd):
    import threading
    popen = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    threading.Thread(target=__output_forwarder,
                     args=[popen.stdout, sys.stdout]).start()
    threading.Thread(target=__output_forwarder,
                     args=[popen.stderr, sys.stderr]).start()
    return_code = popen.wait()
    sys.exit(return_code)


def run(command, **kwargs):
    cmd = ['aprun']
    args = kwargs
    if len(command) == 0:
        logging.critical("No command provided")
        sys.exit(-1)
    num_nodes = args["nodes"]
    num_tasks = args["ntasks"]
    num_tasks_per_node = int(num_tasks/num_nodes)
    cmd += [f'-n {args["ntasks"]}']
    cmd += [f'-N {num_tasks_per_node}']
    extra = args['extra']
    if extra.startswith('"') and extra.endswith('"'):
        extra = extra[1:-1]
    if extra.startswith("'") and extra.endswith("'"):
        extra = extra[1:-1]
    extra = extra.split(',')
    cmd += extra
    cmd += command
    cmd = ' '.join(cmd)
    __run_command_in_subprocess(cmd)
