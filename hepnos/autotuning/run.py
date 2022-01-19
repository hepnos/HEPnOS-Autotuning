import os
import sys
import argparse
import logging
import importlib


def __import_platform():
    platform_name = os.getenv('HEPNOS_EXP_PLATFORM')
    if platform_name is None:
        logging.critical('Could not get platform from HEPNOS_EXP_PLATFORM variable.')
        sys.exit(-1)
    try:
        platform = importlib.import_module('hepnos.autotuning.'+platform_name+'.jobs')
    except ModuleNotFoundError:
        loggin.critical(f'Could not find module corresponding to {platform}')
        sys.exit(-1)
    return platform


if __name__ == '__main__':
    platform = __import_platform()
    parser = argparse.ArgumentParser(description='Run a parallel application')
    parser.add_argument('command', type=str,
                        help="Command to run.",
                        nargs=argparse.REMAINDER)
    parser.add_argument('-n', '--ntasks', required=True, type=int,
                        help="Total number of processes to spawn.")
    parser.add_argument('-N', '--nodes', required=False, type=int,
                        help="Number of nodes to use.")
    args = parser.parse_args()
    platform.run(**vars(args))
