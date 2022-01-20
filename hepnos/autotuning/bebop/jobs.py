import logging
import sys
import os
from ..process import run_command

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



def submit(command, **kwargs):
    cmd = ['sbatch']
    args = kwargs
    if len(command) == 0:
        logging.critical("No command provided")
        sys.exit(-1)
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
    sys.exit(run_command(cmd))
