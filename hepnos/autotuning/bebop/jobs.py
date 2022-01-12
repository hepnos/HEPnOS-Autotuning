import logging
import sys


def generate_preamble(A, t, n, q, **kargs):
    if len(A) == 0:
        logging.critical('Bebop requires an allocation to be provided (-A)')
        sys.exit(-1)
    if len(q) == 0:
        q = 'bdwall'
    preamble = "#!/usr/bin/env bash\n"
    preamble += f"#SBATCH -p bdw\n"
    preamble += f"#SBATCH -N {n}\n"
    preamble += f"#SBATCH -A {A}\n"
    preamble += f"#SBATCH -t {t}\n"
    preamble += f"#SBATCH -q {q}"
    return preamble
