#!/bin/sh

WDIR=`pwd`
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source $WDIR/settings.sh
if [[ -z "${COBALT_JOBID}" ]]; then
  source $WDIR/settings.sh
  JOBID=`qsub -A $HEPNOS_PROJECT $HERE/job.qsub`
  cqwait $JOBID
else
  $HERE/job.qsub
fi
