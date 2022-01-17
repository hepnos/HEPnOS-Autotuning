import logging
import sys


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
