import logging
import sys


def generate_preamble(A, t, n, q, **kwards):
    if len(q) == 0:
        q = 'default' if n >= 128 else 'debug-flat-quad'
    preamble = "#!/usr/bin/env bash\n"
    if len(A) != 0:
        preamble += f"#COBALT -A {A}\n"
    preamble += f"#COBALT -t {t}\n"
    preamble += f"#COBALT -n {n}\n"
    preamble += f"#COBALT -q {q}\n"
    return preamble
