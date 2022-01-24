#!/bin/bash
#H -n 4
#H --time 00:30:00
#H -A radix-io
#H -p bdwall
#H -q debug-flat-quad

HEPNOS_BUILD_PREFIX=${HEPNOS_BUILD_PREFIX:-$1}
EXPDIR=${EXPDIR:-$2}

source $HEPNOS_BUILD_PREFIX/setup-env.sh

NODES_PER_EXP=$SLURM_JOB_NUM_NODES
PROTOCOL=$HEPNOS_LIBFABRIC_PROTOCOL
HEPNOS_CONFIG=$EXPDIR/hepnos.json
LOADER_MARGO_CONFIG=$EXPDIR/dataloader.json
PEP_MARGO_CONFIG=$EXPDIR/pep.json

HEPNOS_SSG=hepnos.ssg
DATABASES_CONFIG=databases.json

rm -f ${DATABASES_CONFIG}

log "Sourcing $EXPDIR/test-settings.sh"
source $EXPDIR/settings.sh

EXTRA_FLAGS=""

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    log "Setting up protection domain"
    HEPNOS_PDOMAIN=${HEPNOS_user_theta_pdomain}
    apstat -P | grep ${HEPNOS_PDOMAIN} || apmgr pdomain -c -u ${HEPNOS_PDOMAIN}
    EXTRA_FLAGS="--extra \"-p,${HEPNOS_PDOMAIN}\""
fi

NUM_NODES_FOR_HEPNOS=$(($NODES_PER_EXP/4))
NUM_NODES_FOR_LOADER=$(($NODES_PER_EXP - $NUM_NODES_FOR_HEPNOS))
NUM_NODES_FOR_PEP=$(($NODES_PER_EXP - $NUM_NODES_FOR_HEPNOS))

if [[ -z "${HEPNOS_NODELIST}" ]]; then
    log "Using default node list"
    NODES_FOR_HEPNOS=""
    NODES_FOR_LOADER=""
    NODES_FOR_PEP=""
    NODE_FOR_UTILITY=""
else
    NUM_NODES=${#HEPNOS_NODELIST[@]}
    if [ $NUM_NODES -ne $NODES_PER_EXP ]; then
        log "ERROR: node list provided should be of length $NODES_PER_EXP"
        exit -1
    fi
    NODES_FOR_HEPNOS=("${HEPNOS_NODELIST[@]:0:$NUM_NODES_FOR_HEPNOS}")
    b=$(printf ",%s" "${NODES_FOR_HEPNOS[@]}")
    b=${b:1}
    NODES_FOR_HEPNOS="--nodelist $b"
    NODES_FOR_LOADER=("${HEPNOS_NODELIST[@]:$NUM_NODES_FOR_HEPNOS}")
    b=$(printf ",%s" "${NODES_FOR_LOADER[@]}")
    b=${b:1}
    NODES_FOR_LOADER="--nodelist $b"
    NODES_FOR_PEP=("${HEPNOS_NODELIST[@]:$NUM_NODES_FOR_HEPNOS}")
    b=$(printf ",%s" "${NODES_FOR_PEP[@]}")
    b=${b:1}
    NODES_FOR_PEP="--nodelist $b"
    NODE_FOR_UTILITY="--nodelist ${HEPNOS_NODELIST[$NUM_NODES_FOR_HEPNOS]}"
fi

if [ "$HEPNOS_ENABLE_PROFILING" -eq "1" ]; then
  export MARGO_ENABLE_DIAGNOSTICS=1
  export MARGO_ENABLE_PROFILING=1
else
  export MARGO_ENABLE_DIAGNOSTICS=0
  export MARGO_ENABLE_PROFILING=0
fi

NUM_PES_FOR_HEPNOS=$((${HEPNOS_PES_PER_NODE} * ${NUM_NODES_FOR_HEPNOS}))
log "Starting up HEPnOS daemon"
HEPNOS_CORES_PER_PE=$(( 32 / $HEPNOS_PES_PER_NODE ))
python3 -m hepnos.autotuning.run -n ${NUM_PES_FOR_HEPNOS} -N ${NUM_NODES_FOR_HEPNOS} ${NODES_FOR_HEPNOS} ${EXTRA_FLAGS} \
        bedrock ${PROTOCOL} -c ${HEPNOS_CONFIG} -v trace &> hepnos-out.txt &
HEPNOS_PID=$!

log "Waiting for HEPnOS daemon to start up"
while [ ! -f ${HEPNOS_SSG} ]; do sleep 1; done

if [ "$HEPNOS_LOADER_ENABLE_PROFILING" -eq "1" ]; then
    export MARGO_ENABLE_DIAGNOSTICS=1
    export MARGO_ENABLE_PROFILING=1
else
    export MARGO_ENABLE_DIAGNOSTICS=0
    export MARGO_ENABLE_PROFILING=0
fi

log "Requesting databases"
timeout ${HEPNOS_UTILITY_TIMEOUT} \
    python3 -m hepnos.autotuning.run -n 1 -N 1 ${NODES_FOR_UTILITY} ${EXTRA_FLAGS} hepnos-list-databases \
    ${PROTOCOL} -s ${HEPNOS_SSG} > ${DATABASES_CONFIG}

RET=$?
if [ "$RET" -eq "124" ]; then
    log "ERROR: hepnos-list-databases timed out"
    kill $HEPNOS_PID
    exit -1
fi

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    sed -i '$ d' ${DATABASES_CONFIG} # we have to because aprun adds a line
fi

LOADER_PRODUCT_ARGS=""
for p in ${HEPNOS_LOADER_PRODUCTS[@]}; do
    LOADER_PRODUCT_ARGS="${LOADER_PRODUCT_ARGS} -n ${p}"
done

log "Starting dataloader"
NUM_PES_FOR_LOADER=$(( $NUM_NODES_FOR_LOADER * $HEPNOS_LOADER_PES_PER_NODE ))
LOADER_CORES_PER_PE=$(( 32 / $HEPNOS_LOADER_PES_PER_NODE ))
start_time=`date +%s`
timeout ${HEPNOS_LOADER_TIMEOUT} \
    python3 -m hepnos.autotuning.run -n ${NUM_PES_FOR_LOADER} -N ${NUM_NODES_FOR_LOADER} ${NODES_FOR_LOADER} ${EXTRA_FLAGS} \
             hepnos-dataloader \
             --timeout ${HEPNOS_LOADER_SOFT_TIMEOUT} \
             -p ${PROTOCOL} \
             -m ${LOADER_MARGO_CONFIG} \
             -c ${DATABASES_CONFIG} \
             -i ${HEPNOS_LOADER_DATAFILE} \
             -o ${HEPNOS_DATASET} \
             -l ${HEPNOS_LABEL} \
             -b ${HEPNOS_LOADER_BATCH_SIZE} \
             ${HEPNOS_LOADER_ASYNC} \
             -t ${HEPNOS_LOADER_ASYNC_THREADS} \
             ${LOADER_PRODUCT_ARGS} \
             -v ${HEPNOS_LOADER_VERBOSE} \
             &>> $EXPDIR/dataloader-output.txt
RET=$?
end_time=`date +%s`
if [ "$RET" -eq "124" ]; then
    log "ERROR: hepnos-dataloader timed out"
    echo "RUNTIME: ${CONST_TIMEOUT}" >> $EXPDIR/dataloader-output.txt
    kill $HEPNOS_PID
    exit -1
fi
if grep -q "ESTIMATED" $EXPDIR/dataloader-output.txt
then
    runtime=$((end_time-start_time))
    echo "RUNTIME: ${runtime}" >> $EXPDIR/dataloader-output.txt
else
    log "ERROR: hepnos-dataloader failed"
    echo "RUNTIME: ${CONST_FAILURE}" >> $EXPDIR/dataloader-output.txt
    kill $HEPNOS_PID
    exit -1
fi

if [ "$HEPNOS_ENABLE_PEP" -ne "0" ]; then
    NUM_PES=$(($HEPNOS_PEP_PES_PER_NODE * $NUM_NODES_FOR_PEP))
    PEP_PRODUCT_ARGS=""
    for p in ${HEPNOS_PEP_PRODUCTS[@]}; do
      PEP_PRODUCT_ARGS="${PEP_PRODUCT_ARGS} -n ${p}"
    done

    if [ "$HEPNOS_PEP_ENABLE_PROFILING" -eq "1" ]; then
        export MARGO_ENABLE_DIAGNOSTICS=1
        export MARGO_ENABLE_PROFILING=1
    else
        export MARGO_ENABLE_DIAGNOSTICS=0
        export MARGO_ENABLE_PROFILING=0
    fi

    log "Running PEP benchmark"
    PEP_CORES_PER_PE=$(( 32 / $HEPNOS_PEP_PES_PER_NODE ))
    start_time=`date +%s`
    timeout ${HEPNOS_PEP_TIMEOUT} \
    python3 -m hepnos.autotuning.run -n ${NUM_PES} -N ${NUM_NODES_FOR_PEP} ${NODES_FOR_PEP} ${EXTRA_FLAGS} \
             hepnos-pep-benchmark \
             -p ${PROTOCOL} \
             -m ${PEP_MARGO_CONFIG} \
             -c ${DATABASES_CONFIG} \
             -d ${HEPNOS_DATASET} \
             -l ${HEPNOS_LABEL} \
             ${PEP_PRODUCT_ARGS} \
             ${HEPNOS_PEP_PRELOAD} \
             -v ${HEPNOS_PEP_VERBOSE} \
             -o ${HEPNOS_PEP_OBATCH_SIZE} \
             -i ${HEPNOS_PEP_IBATCH_SIZE} \
             -t ${HEPNOS_PEP_THREADS} \
             &>> $EXPDIR/pep-output.txt
    RET=$?
    end_time=`date +%s`
    if [ "$RET" -eq "124" ]; then
        log "ERROR: hepnos-pep timed out"
        echo "TIME: ${CONST_TIMEOUT}" >> $EXPDIR/pep-output.txt
        kill -- -$HEPNOS_PID
        exit -1
    fi
    if grep -q "Benchmark completed" $EXPDIR/pep-output.txt
    then
        runtime=$((end_time-start_time))
        echo "TIME: ${runtime}" >> $EXPDIR/pep-output.txt
    else
        log "ERROR: hepnos-pep failed"
        echo "TIME: ${CONST_FAILURE}" >> $EXPDIR/pep-output.txt
        kill $HEPNOS_PID
        exit -1
    fi
fi

log "Shutting down HEPnOS"
timeout ${HEPNOS_UTILITY_TIMEOUT} \
        python3 -m hepnos.autotuning.run -n 1 -N 1 ${NODES_FOR_UTILITY} ${EXTRA_FLAGS} \
        hepnos-shutdown $PROTOCOL $DATABASES_CONFIG
RET=$?
if [ "$RET" -eq "124" ]; then
    log "ERROR: hepnos-shutdown timed out"
    kill $HEPNOS_PID
    exit -1
fi

if [ $HEPNOS_EXP_PLATFORM == "theta" ]; then
    log "Removing protection domain"
    apmgr pdomain -r -u ${HEPNOS_PDOMAIN}
fi

