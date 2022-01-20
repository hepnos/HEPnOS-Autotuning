import threading
import subprocess
import sys

def __output_forwarder(pipe, out):
    try:
        with pipe:
            for line in iter(pipe.readline, b''):
                out.write(line.decode())
    finally:
        pass


def run_command(cmd):
    popen = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    threading.Thread(target=__output_forwarder,
                     args=[popen.stdout, sys.stdout]).start()
    threading.Thread(target=__output_forwarder,
                     args=[popen.stderr, sys.stderr]).start()
    return popen.wait()
