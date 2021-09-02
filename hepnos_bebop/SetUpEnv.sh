#!/bin/bash

module load gcc/8.2.0-g7hppkz

. $HOME/HEPnOS-Autotuning/hepnos_bebop/spack/share/spack/setup-env.sh

# Activate spackenvironment
spack env activate hepnos

# Activate conda env
conda activate $HOME/exp-hep/dhenv/

export PYTHONPATH="$HOME/HEPnOS-Autotuning/:$PYTHONPATH"
