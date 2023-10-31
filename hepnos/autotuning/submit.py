import os
import sys
import argparse
import logging
from .platform import detect_platform
from .header import get_flags_from_header

if __name__ == '__main__':
    platform = detect_platform()
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
    args_from_cmd_line = parser.parse_args()
    filename = args_from_cmd_line.command[0]
    args_from_script = parser.parse_args(get_flags_from_header(filename))
    full_args = {}
    for k,v in vars(args_from_script).items():
        full_args[k] = v
    for k,v in vars(args_from_cmd_line).items():
        if v is not None:
            full_args[k] = v
    platform.submit(**full_args)
