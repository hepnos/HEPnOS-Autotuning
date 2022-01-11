#!/bin/bash

set -e

if [ $# -eq 0 ]
then
    echo "Platform not specified"
    exit -1
fi

WD=`pwd`
HERE=`dirname "$(realpath $0)"`

PLATFORM=$1
if [ ! -d $HERE/hepnos/autotuning/$PLATFORM ]
then
    echo "Unknown platform ($PLATFORM)"
    exit -1
fi

PLATFORM_PATH=$HERE/hepnos/autotuning/$PLATFORM

function log {
    printf "\u2550\u2550> $1\n"
}

function download_from_git {
    NAME=$1
    URL=$2
    REF=$3
    log "Cloning $NAME repo ($URL)..."
    git clone $URL
    log "Checking out $REF..."
    pushd $NAME
    git checkout $REF
    popd
}

function install_with_pip {
    NAME=$1
    pushd $NAME
    log "Installing $NAME with pip..."
    pip install -e.
    popd
}

log "Sourcing global settins..."
source $HERE/settings.sh

log "Sourcing $PLATFORM-specific settings..."
if test -f "$PLATFORM_PATH/settings.sh"; then
    source $PLATFORM_PATH/settings.sh
fi

log "Creating sw directory..."
mkdir sw
pushd sw

download_from_git spack $SPACK_GIT $SPACK_REF

log "Setting up spack..."
. ./spack/share/spack/setup-env.sh

download_from_git mochi-spack-packages $MOCHI_REPO_GIT $MOCHI_REPO_REF

log "Creating hepnos environment using $PLATFORM_PATH/spack.yaml..."
spack env create hepnos $PLATFORM_PATH/spack.yaml

log "Activating hepnos environment..."
spack env activate hepnos

log "Adding mochi repo to environment..."
spack repo add $WD/sw/mochi-spack-packages

log "Adding specs to environment..."
cat $HERE/spack-requirements.txt | while read dependency
do
   spack add $dependency
done

log "Adding $PLATFORM-specific specs to environment..."
if test -f "$PLATFORM_PATH/requirements.txt"; then
    cat $PLATFORM_PATH/spack-requirements.txt | while read dependency
    do
        spack add $dependency
    done
fi

log "Installing spack environment..."
spack install

log "Creating a miniconda environment..."
CONDA_PREFIX=`spack location -i miniconda3`
source $CONDA_PREFIX/etc/profile.d/conda.sh
conda create -p $WD/sw/dhenv python=3.9 gxx_linux-64 gcc_linux-64 pip -y
conda activate $WD/sw/dhenv/

if test -f "$HERE/pip-requirements.$PLATFORM.lock"; then
    log "Creating conda environment using pip-requirements.$PLATFORM.lock..."
    pip install -r $HERE/pip-requirements.$PLATFORM.lock
else
    log "Creating conda environment using pip-requirements.txt..."
    pip install -r $HERE/pip-requirements.txt
    log "Generating pip-requirements.$PLATFORM.lock for reproducibility..."
    pip freeze > $HERE/pip-requirements.$PLATFORM.lock
fi

popd # sw
