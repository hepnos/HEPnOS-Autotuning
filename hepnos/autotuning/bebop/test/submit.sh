#!/usr/bin/env bash

if [ -z "$HEPNOS_BUILD_PREFIX" ]; then
    echo "ERROR: please source setup-env.sh first"
    exit -1
fi

HERE=`dirname "$(realpath $0)"`
export EXPDIR=`pwd`

$HERE/cleanup.sh

sbatch --export ALL $HERE/job.sbatch
