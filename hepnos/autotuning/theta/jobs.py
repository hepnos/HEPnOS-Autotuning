import logging
import sys


def generate_preamble(A, t, n, q, **kwards):
    if len(A) == 0:
        logging.critical('Theta requires an allocation to be provided (-A)')
        sys.exit(-1)
    if len(q) == 0:
        q = 'default' if n >= 128 else 'debug-flat-quad'
    preamble = "#!/usr/bin/env bash\n"
    preamble += f"#COBALT -A {A}\n"
    preamble += f"#COBALT -t {t}\n"
    preamble += f"#COBALT -n {n}\n"
    preamble += f"#COBALT -q {q}\n"
    return preamble
