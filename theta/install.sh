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
spack compiler find

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

log "Installing HEPnOS, DataLoader, and PEP..."
spack install
