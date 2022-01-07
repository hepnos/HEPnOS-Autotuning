#!/bin/bash

set -e

function log {
    printf "\u2550\u2550> $1\n"
}

WD=`pwd`
log "Cloning spack..."
git clone https://github.com/spack/spack.git

log "Setting up spack..."
. ./spack/share/spack/setup-env.sh

log "Cloning mochi namespace..."
git clone https://github.com/mochi-hpc/mochi-spack-packages.git

log "Creating hepnos environment..."
spack env create hepnos env/spack.yaml

log "Activating hepnos environment..."
spack env activate hepnos

log "Adding mochi repo to environment..."
spack repo add $WD/mochi-spack-packages

log "Installing miniconda, HEPnOS, DataLoader, and PEP..."
spack install

spack env deactivate
spack env activate hepnos

log "Creating a miniconda environment for Python packages..."
conda create -p dhenv python=3.9 -y
CONDA_PREFIX=`spack location -i miniconda3`
source $CONDA_PREFIX/etc/profile.d/conda.sh
conda activate dhenv/
conda install gxx_linux-64 gcc_linux-64 -y

mkdir dhenv-sources
pushd dhenv-sources

log "Cloning ConfigSpace repo and installing..."
git clone https://github.com/deephyper/ConfigSpace.git
pushd ConfigSpace
git checkout truncated_normal
pip install -e.
popd

log "Cloning Scikit-Optimize repo and installing..."
git clone https://github.com/deephyper/scikit-optimize.git
pushd scikit-optimize
pip install -e.
popd

log "Cloning DeepHyper repo and installing..."
git clone https://github.com/deephyper/deephyper.git
pushd deephyper
git checkout develop
pip install -e.
popd

log "Cloning py-mochi-bedrock and installing..."
git clone https://github.com/mochi-hpc/py-mochi-bedrock.git
pushd py-mochi-bedrock
pip install -e.
popd

log "Cloning hepnos-wizard and installing..."
git clone https://github.com/hepnos/HEPnOS-Wizard.git
pushd HEPnOS-Wizard
pip install -e.
popd

popd # dhenv-sources
