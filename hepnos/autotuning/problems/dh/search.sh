#!/bin/bash
#H -n 128
#H --time 01:00:00
#H -A radix-io
#H -p bdwall

###H -q debug-flat-quad

HEPNOS_BUILD_PREFIX=${1:-$HEPNOS_BUILD_PREFIX}
shift
EXPDIR=${1:-$EXPDIR}
shift

NODES_PER_EXP=${1:-${HEPNOS_NODES_PER_EXP:-4}}
shift
ENABLE_PEP=${1:-${HEPNOS_EXP_ENABLE_PEP:-true}}
shift
MORE_PARAMS=${1:-${HEPNOS_EXP_MORE_PARAMS:-true}}
shift
EXTRA=$@

source $HEPNOS_BUILD_PREFIX/setup-env.sh

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    log "Setting up protection domain"
    HEPNOS_PDOMAIN=${HEPNOS_user_theta_pdomain}
    apstat -P | grep ${HEPNOS_PDOMAIN} || apmgr pdomain -c -u ${HEPNOS_PDOMAIN}
fi
export HEPNOS_PDOMAIN_READY=true

if [ "$ENABLE_PEP" = false ]; then
    DISABLE_PEP="--disable_pep"
else
    DISABLE_PEP=""
fi

if [ "$MORE_PARAMS" = true ]; then
    MORE_PARAMS="--more_params"
else
    MORE_PARAMS=""
fi

log "Starting DeepHyper search"

python3 -m hepnos.autotuning.search --problem hepnos.autotuning.problems.simple \
        --nodes_per_exp ${NODES_PER_EXP} ${DISABLE_PEP} ${MORE_PARAMS} ${EXTRA}

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    log "Removing protection domain"
    apmgr pdomain -r -u ${HEPNOS_PDOMAIN}
fi

