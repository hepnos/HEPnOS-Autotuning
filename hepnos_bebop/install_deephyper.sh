#!/bin/bash

HERE=`dirname $0`
HERE=`realpath $HERE`

function log {
    printf "\u2550\u2550> $1\n"
}

module load gcc/8.2.0-g7hppkz

# Create Conda Env
log "Loading modules and creating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda create -p dhenv python=3.8 -y
conda activate dhenv/
conda install gxx_linux-64 gcc_linux-64 -y

# Install ConfigSpace with Truncated Normal Distribution
log "Cloning ConfigSpace repo and installing..."
git clone https://github.com/deephyper/ConfigSpace.git
cd ConfigSpace/
git checkout truncated_normal
pip install -e.
cd ..

# Installing Scikit-Optimize with ConfigSpace
log "Cloning Scikit-Optimize repo and installing..."
git clone https://github.com/deephyper/scikit-optimize.git
cd scikit-optimize/
pip install -e.
cd ..

# Install DeepHyper
log "Cloning DeepHyper repo and installing..."
#git clone https://github.com/pbalapra/deephyper.git
git clone https://github.com/mdorier/deephyper.git
cd deephyper/
#git checkout develop
git checkout dev-add-slurm-nodes
pip install -e.
cd ..

