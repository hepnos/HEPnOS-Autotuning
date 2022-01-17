import logging
import sys


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
