

def generate_preamble(A, t, n, q, **kwards):
    preamble = "#!/usr/bin/env bash\n"
    preamble += f"#COBALT -A {A}\n"
    preamble += f"#COBALT -t {t}\n"
    preamble += f"#COBALT -n {n}\n"
    preamble += f"#COBALT -q {q}\n"
    return preamble
