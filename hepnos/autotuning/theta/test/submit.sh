#!/usr/bin/env bash

if [ -z "$HEPNOS_BUILD_PREFIX" ]; then
    echo "ERROR: please source setup-env.sh first"
    exit -1
fi

qsub --env "EXPDIR=`pwd`" --env "HEPNOS_BUILD_PREFIX=$HEPNOS_BUILD_PREFIX" job.qsub
