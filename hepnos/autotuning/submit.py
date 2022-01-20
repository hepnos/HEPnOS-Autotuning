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
    parser = argparse.ArgumentParser(description='Submit a job')
    parser.add_argument('command', type=str,
                        help="Command to submit.",
                        nargs=argparse.REMAINDER)
    parser.add_argument('-A', '--allocation', required=False, type=str,
                        help="Project allocation.")
    parser.add_argument('-t', '--time', required=False, type=str,
                        help="Job run time.")
    parser.add_argument('-n', '--nodes', required=False, type=str,
                        help="Number of nodes to allocate for the job.")
    parser.add_argument('-q', '--queue', required=False, type=str,
                        help="Queue on which to run the job.")
    parser.add_argument('-p', '--partition', required=False, type=str,
                        help="Partition in which to run the job.")
    parser.add_argument('--extra', required=False, type=str, default='',
                        help="Extra arguments to pass to the job management system.")
    args = parser.parse_args()
    platform.submit(**vars(args))
