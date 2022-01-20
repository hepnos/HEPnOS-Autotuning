#!/usr/bin/env bash

if [ -z "$HEPNOS_BUILD_PREFIX" ]; then
    echo "ERROR: please source setup-env.sh first"
    exit -1
fi

HERE=`dirname "$(realpath $0)"`
export EXPDIR=`pwd`

$HERE/cleanup.sh

python -m hepnos.autotuning.submit $HERE/job.sh $HEPNOS_BUILD_PREFIX $EXPDIR
