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
git clone https://xgitlab.cels.anl.gov/sds/sds-repo.git

log "Creating hepnos environment..."
MOCHI_REPO=$WD/sds-repo
cat env/spack.yaml.in \
    | sed -e "s|\${MOCHI_REPO}|${MOCHI_REPO}|g" \
    > env/spack.yaml
spack env create hepnos env/spack.yaml

log "Activating hepnos environment..."
spack env activate hepnos

log "Installing HEPnOS and DataLoader..."
spack install
