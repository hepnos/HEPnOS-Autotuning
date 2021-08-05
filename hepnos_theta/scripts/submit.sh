#!/bin/sh

EXPDIR=$1
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source $EXPDIR/settings.sh
export SCRIPTDIR
export EXPDIR

if [[ -z "${COBALT_JOBID}" ]]; then
  JOBID=`qsub -A $HEPNOS_PROJECT --env "EXPDIR=$EXPDIR:SCRIPTDIR=$SCRIPTDIR" $SCRIPTDIR/$HEPNOS_JOBFILE`
  cqwait $JOBID
else
  $SCRIPTDIR/$HEPNOS_JOBFILE
fi
