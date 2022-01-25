#!/usr/bin/env bash

if [ -z "$HEPNOS_BUILD_PREFIX" ]; then
    echo "ERROR: please source setup-env.sh first"
    exit -1
fi

HERE=`dirname "$(realpath $0)"`
export EXPDIR=`pwd`

eval PROJECT='$'HEPNOS_user_${HEPNOS_EXP_PLATFORM}_project

$HERE/cleanup.sh

python -m hepnos.autotuning.submit -A $PROJECT $HERE/job.sh $HEPNOS_BUILD_PREFIX $EXPDIR
