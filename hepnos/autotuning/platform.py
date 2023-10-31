"""This module provides a function to detect the platform (via the HEPNOS_EXP_PLATFORM
environment variable) and import the corresponding module (theta or bebop)."""

import importlib
import logging
import sys
import os


def detect_platform():
    platform_name = os.getenv('HEPNOS_EXP_PLATFORM')
    if platform_name is None:
        logging.critical('Could not get platform from HEPNOS_EXP_PLATFORM variable.')
        sys.exit(-1)
    try:
        platform = importlib.import_module('hepnos.autotuning.'+platform_name+'.jobs')
    except ModuleNotFoundError:
        logging.critical(f'Could not find module corresponding to {platform}')
        sys.exit(-1)
    return platform
