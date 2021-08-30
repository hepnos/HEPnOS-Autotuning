#!/bin/sh

EXPDIR=$1
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source $EXPDIR/settings.sh
export SCRIPTDIR
export EXPDIR

if [[ -z "${SLURM_JOB_ID}" ]]; then
	sbatch --wait --export=ALL $SCRIPTDIR/job.sbatch || true
else
	$SCRIPTDIR/job.sbatch
fi
