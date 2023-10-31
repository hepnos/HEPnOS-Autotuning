import logging
import sys
import os
import subprocess
from ..process import run_command


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


def get_nodelist():
    import os
    nidstr = os.environ.get('COBALT_PARTNAME', None)
    nidlst = []
    if nidstr is None:
        return nidlst
    nidgroups = nidstr.split(',')
    for nidgroup in nidgroups:
        if (nidgroup.find("-") != -1):
            a, b = nidgroup.split("-", 1)
            a = int(a)
            b = int(b)
            if (a > b):
                tmp = b
                b = a
                a = tmp
            b = b + 1 #need one more for inclusive
        else:
            a = int(nidgroup)
            b = a + 1
        for nid in range(a, b):
            nidlst.append(nid)
    nidlst = [str(x) for x in sorted(list(set(nidlst)))]
    return nidlst


def submit(command, **kwargs):
    cmd = ['qsub']
    args = kwargs
    if len(command) == 0:
        logging.critical("No command provided")
        sys.exit(-1)
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


def run(command, **kwargs):
    cmd = ['aprun']
    args = kwargs
    if len(command) == 0:
        logging.critical("No command provided")
        sys.exit(-1)
    num_nodes = args["nodes"]
    num_tasks = args["ntasks"]
    num_tasks_per_node = int(num_tasks/num_nodes)
    num_cores_per_task = int(64/num_tasks_per_node)
    cmd += [f'-n {args["ntasks"]}']
    cmd += [f'-N {num_tasks_per_node}']
    cmd += [f'-d {num_cores_per_task} -cc none']
    if args['nodelist'] is not None:
        cmd += [f'-L {args["nodelist"]}']
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
