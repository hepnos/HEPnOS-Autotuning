#!/usr/bin/env bash

WD=`pwd`

function log {
    printf "\u2550\u2550> $1\n"
}

log "Sourcing global settings..."
source $WD/global-settings.sh

log "Sourcing platform-specific settings..."
source $WD/platform-settings.sh

log "Found platform to be $HEPNOS_EXP_PLATFORM"

log "Setting up spack..."
. $WD/sw/spack/share/spack/setup-env.sh

log "Activating hepnos environment in spack..."
spack env activate hepnos

log "Activating dhenv environment in conda..."
CONDA_PREFIX=`spack location -i miniconda3`
source $CONDA_PREFIX/etc/profile.d/conda.sh
conda activate $WD/sw/dhenv/

log "Adding $HEPNOS_EXP_SOURCE_PATH to PYTHONPATH"
export PYTHONPATH=$PYTHONPATH:$HEPNOS_EXP_SOURCE_PATH
