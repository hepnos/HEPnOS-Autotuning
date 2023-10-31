"""
This module allows to call a platform-specific "mpirun" command,
such as "aprun" on Theta or "srun" on Bebop, using uniform arguments
that are then translated into platform-specific ones.
"""
import os
import sys
import argparse
import logging
from .platform import detect_platform


if __name__ == '__main__':
    platform = detect_platform()
    parser = argparse.ArgumentParser(description='Run a parallel application')
    parser.add_argument('command', type=str,
                        help="Command to run.",
                        nargs=argparse.REMAINDER)
    parser.add_argument('-n', '--ntasks', required=True, type=int,
                        help="Total number of processes to spawn.")
    parser.add_argument('-N', '--nodes', required=False, type=int,
                        help="Number of nodes to use.")
    parser.add_argument('--nodelist', required=False, type=str,
                        help="Comma-separated list of nodes to use.")
    parser.add_argument('--extra', required=False, type=str, default='',
                        help="Extra arguments to pass to the deployment system.")
    args = parser.parse_args()
    platform.run(**vars(args))
