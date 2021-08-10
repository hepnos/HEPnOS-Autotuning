#!/bin/bash

function log {
    printf "\u2550\u2550> $1\n"
}

# Create Conda Env
log "Loading modules and creating conda environment..."
module load miniconda-3
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

# Install DeepHyper
log "Cloning DeepHyper repo and installing..."
git clone https://github.com/pbalapra/deephyper.git
cd deephyper/
git checkout develop
pip install -e.
cd ..

