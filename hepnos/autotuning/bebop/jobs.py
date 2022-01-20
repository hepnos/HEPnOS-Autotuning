import logging
import sys
import os
import subprocess


def generate_preamble(A, t, n, q, **kargs):
    """Generates the header of the job script."""
    if len(q) == 0:
        q = 'bdwall'
    preamble = "#!/usr/bin/env bash\n"
    preamble += f"#SBATCH -p bdw\n"
    preamble += f"#SBATCH -N {n}\n"
    if len(A) != 0:
        preamble += f"#SBATCH -A {A}\n"
    preamble += f"#SBATCH -t {t}\n"
    preamble += f"#SBATCH -q {q}"
    return preamble


def generate_prologue(**kwargs):
    """Generates the prologue for the job."""
    return ''


def generate_epilogue(**kwargs):
    """Generate the epilogue for the job."""
    return ''


def generate_mpirun(program, num_nodes, pes_per_node, **kwargs):
    """Generate an mpirun command for the platform."""
    num_pes = num_nodes*pes_per_node
    cmd = f'srun --exclusive -n {num_pes} -N {num_nodes} '
    if 'node_list' in kwargs:
        node_list = kwargs['node_list']
        if isinstance(node_list, list):
            nodes = ','.join(node_list)
            cmd += f'--nodelist {nodes} '
        else:
            cmd += f'--nodelist {node_list} '
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
        if line.startswith('#!'):
            if interpreter_dir:
                return args
            else:
                interpreter_dir = True
            continue
        elif line.startswith('#H '):
            elems = line.split()[1:]
            if len(elems) != 2:
                raise ValueError(f'Invalid header line {line}')
            flag = elems[0]
            value = elems[1]
            if flag in flag_translation:
                result[flag_translation[flag]] = value
        else:
            break
    return result


def submit(command, **kwargs):
    cmd = ['sbatch']
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
        cmd += [f'-N {args["nodes"]}']
    if args['partition'] is not None:
        cmd += [f'-p {args["partition"]}']
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
    cmd = ['srun', '--exclusive']
    args = kwargs
    if len(command) == 0:
        logging.critical("No command provided")
        sys.exit(-1)
    cmd += [f'-n {args["ntasks"]}']
    cmd += [f'-N {args["nodes"]}']
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
