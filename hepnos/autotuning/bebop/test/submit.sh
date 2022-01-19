#!/usr/bin/env bash

if [ -z "$HEPNOS_BUILD_PREFIX" ]; then
    echo "ERROR: please source setup-env.sh first"
    exit -1
fi

HERE=`dirname "$(realpath $0)"`
export EXPDIR=`pwd`

$HERE/cleanup.sh

#python -m hepnos.autotuning.submit --nodes 4 --time 00:10:00 --partition bdwall -A radix-io \
#	       $HERE/job.sbatch
python -m hepnos.autotuning.submit $HERE/job.sbatch

#sbatch $HERE/job.sbatch
