#!/bin/sh

function log {
    printf "\u2550\u2550> $1\n"
}

WD=`pwd`
log "Cloning spack..."
git clone https://github.com/spack/spack.git

log "Setting up spack..."
. ./spack/share/spack/setup-env.sh

log "Finding compilers..."
module load gcc/8.2.0-g7hppkz
#spack compiler find

log "Cloning mochi namespace..."
git clone https://github.com/mochi-hpc/mochi-spack-packages.git

log "Creating hepnos environment..."
MOCHI_REPO=$WD/mochi-spack-packages
cat env/spack.yaml.in \
    | sed -e "s|\${MOCHI_REPO}|${MOCHI_REPO}|g" \
    > env/spack.yaml
spack env create hepnos env/spack.yaml

log "Activating hepnos environment..."
spack env activate hepnos

log "Installing HEPnOS and DataLoader..."
spack install

# Create Conda Env
log "Creating conda environment..."
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
git clone https://github.com/pbalapra/deephyper.git
cd deephyper/
git checkout develop
pip install -e.
cd ..
