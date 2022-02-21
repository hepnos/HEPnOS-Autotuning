#!/bin/bash
#H -n 128
#H --time 01:00:00
#H -A radix-io
#H -p bdwall

###H -q debug-flat-quad

HEPNOS_BUILD_PREFIX=${1:-$HEPNOS_BUILD_PREFIX}
EXPDIR=${2:-$EXPDIR}

NODES_PER_EXP=${3:-${HEPNOS_NODES_PER_EXP:-4}}

source $HEPNOS_BUILD_PREFIX/setup-env.sh

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    log "Setting up protection domain"
    HEPNOS_PDOMAIN=${HEPNOS_user_theta_pdomain}
    apstat -P | grep ${HEPNOS_PDOMAIN} || apmgr pdomain -c -u ${HEPNOS_PDOMAIN}
    EXTRA_FLAGS="--extra \"-p,${HEPNOS_PDOMAIN}\""
fi
export HEPNOS_PDOMAIN_READY=true

log "Starting DeepHyper search"

python3 -m hepnos.autotuning.search --problem hepnos.autotuning.problems.simple \
        --nodes_per_exp ${NODES_PER_EXP}

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    log "Removing protection domain"
    apmgr pdomain -r -u ${HEPNOS_PDOMAIN}
fi

