#!/usr/bin/env bash

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

# Copying the util directory into the build directory
# since these scripts will be used at run time.
cp -r $HERE/util $WD

source $WD/util/logging.sh
source $WD/util/git.sh
source $WD/util/yaml.sh

if [ -f "$WD/sources.yaml.lock" ]; then
    log "Parsing sources settings from $WD/sources.yaml.lock..."
    eval $(parse_yaml $WD/sources.yaml.lock "SOURCES_")
else
    log "Parsing sources settings from $HERE/sources.yaml..."
    eval $(parse_yaml $HERE/sources.yaml "SOURCES_")
fi

PLATFORM_SETTINGS=$HERE/hepnos/autotuning/$PLATFORM/settings.sh
PLATFORM_SPACKENV=$HERE/hepnos/autotuning/$PLATFORM/spack.yaml

log "Sourcing $PLATFORM-specific install settings..."
if [ -f "$PLATFORM_SETTINGS" ]; then
    source $PLATFORM_SETTINGS
fi

log "Creating sw directory..."
mkdir sw
pushd sw

download_from_git spack $SOURCES_spack_git $SOURCES_spack_ref

log "Setting up spack..."
. ./spack/share/spack/setup-env.sh

download_from_git mochi-spack-packages $SOURCES_mochi_git $SOURCES_mochi_ref

if [ ! -f "$WD/sources.yaml.lock" ]; then
    log "Generating sources.yaml.lock for reproducibility..."
    pushd spack
    spack_commit=$(git rev-parse HEAD)
    popd
    pushd mochi-spack-packages
    mochi_commit=$(git rev-parse HEAD)
    popd
    echo "spack:" >> $WD/sources.yaml.lock
    echo "  git: $SOURCES_spack_git" >> $WD/sources.yaml.lock
    echo "  ref: $spack_commit" >> $WD/sources.yaml.lock
    echo "mochi:" >> $WD/sources.yaml.lock
    echo "  git: $SOURCES_mochi_git" >> $WD/sources.yaml.lock
    echo "  ref: $mochi_commit" >> $WD/sources.yaml.lock
fi

log "Creating hepnos environment using $PLATFORM_SPACKENV..."
spack env create hepnos $PLATFORM_SPACKENV

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

if test -f "$WD/pip-requirements.txt.lock"; then
    log "Creating conda environment using pip-requirements.txt.lock..."
    pip install -r $WD/pip-requirements.txt.lock
else
    log "Creating conda environment using pip-requirements.txt..."
    pip install -r $HERE/pip-requirements.txt
    log "Generating pip-requirements.lock for reproducibility..."
    pip freeze > $WD/pip-requirements.txt.lock
fi

popd # sw

##############################################################
# setup-env.sh
##############################################################
cat > $WD/setup-env.sh <<- EndOfSetup
#!/usr/bin/env bash

source $WD/util/logging.sh
source $WD/util/git.sh
source $WD/util/yaml.sh

log "Setting up spack..."
. $WD/sw/spack/share/spack/setup-env.sh

log "Activating hepnos environment in spack..."
spack env activate hepnos

log "Activating dhenv environment in conda..."
source $CONDA_PREFIX/etc/profile.d/conda.sh
conda activate $WD/sw/dhenv/

export PYTHONPATH=\$PYTHONPATH:$HERE
export HEPNOS_EXP_PLATFORM=$PLATFORM

EndOfSetup
##############################################################
