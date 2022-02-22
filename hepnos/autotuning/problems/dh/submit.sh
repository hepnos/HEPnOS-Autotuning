#!/usr/bin/env bash

if [ -z "$HEPNOS_BUILD_PREFIX" ]; then
    echo "ERROR: please source setup-env.sh first"
    exit -1
fi

HERE=`dirname "$(realpath $0)"`
export EXPDIR=`pwd`

eval PROJECT='$'HEPNOS_user_${HEPNOS_EXP_PLATFORM}_project

NODES_PER_EXP=${1:-${HEPNOS_NODES_PER_EXP:-4}}
ENABLE_PEP=${2:-${HEPNOS_EXP_ENABLE_PEP:-true}}
MORE_PARAMS=${3:-${HEPNOS_EXP_MORE_PARAMS:-true}}

python -m hepnos.autotuning.submit -A $PROJECT $HERE/search.sh \
               $HEPNOS_BUILD_PREFIX $EXPDIR \
               $NODES_PER_EXP \
               $ENABLE_PEP \
               $MORE_PARAMS
