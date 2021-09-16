#!/bin/bash
#SBATCH -N 4
#SBATCH --time=30:00
#SBATCH -p bdwall
#SBATCH -A radix-io

#set -e
PROTOCOL=ofi+psm2
HEPNOS_CONFIG=$EXPDIR/hepnos.json
HEPNOS_SSG=$EXPDIR/hepnos.ssg
DATABASES_CONFIG=$EXPDIR/databases.json
LOADER_MARGO_CONFIG=$EXPDIR/dataloader.json
PEP_MARGO_CONFIG=$EXPDIR/pep.json

module load gcc/8.2.0-xhxgy33

export PSM2_MULTI_EP=1

export MARGO_OUTPUT_DIR=$EXPDIR
rm -f ${DATABASES_CONFIG}

echo "Sourcing settings"
source $EXPDIR/settings.sh

NUM_NODES_FOR_HEPNOS=$(($NODES_PER_EXP/4))
NUM_NODES_FOR_LOADER=$(($NODES_PER_EXP - $NUM_NODES_FOR_HEPNOS))
NUM_NODES_FOR_PEP=$(($NODES_PER_EXP - $NUM_NODES_FOR_HEPNOS))

if [[ -z "${HEPNOS_NODELIST}" ]]; then
    echo "Using default node list"
    NODES_FOR_HEPNOS=""
    NODES_FOR_LOADER=""
    NODES_FOR_PEP=""
    NODE_FOR_UTILITY=""
else
    NUM_NODES=${#HEPNOS_NODELIST[@]}
    if [ $NUM_NODES -ne $NODES_PER_EXP ]; then
        echo "ERROR: node list provided should be of length $NODES_PER_EXP"
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

echo "NODES_FOR_HEPNOS = ${NODES_FOR_HEPNOS}"
echo "NODE_FOR_UTILITY = ${NODE_FOR_UTILITY}"
echo "NODES_FOR_LOADER = ${NODES_FOR_LOADER}"
echo "NODES_FOR_PEP = ${NODES_FOR_PEP}"

echo "Setting up spack and modules"
source $SCRIPTDIR/../spack/share/spack/setup-env.sh

echo "Activating spack env"
spack env activate hepnos
spack load -r hepnos
spack load -r hepnos-dataloader
spack load -r hepnos-pep-benchmark

if [ "$HEPNOS_ENABLE_PROFILING" -eq "1" ]; then
  export MARGO_ENABLE_DIAGNOSTICS=1
  export MARGO_ENABLE_PROFILING=1
else
  export MARGO_ENABLE_DIAGNOSTICS=0
  export MARGO_ENABLE_PROFILING=0
fi

NUM_PES_FOR_HEPNOS=$((${HEPNOS_PES_PER_NODE} * ${NUM_NODES_FOR_HEPNOS}))
echo "Starting up HEPnOS daemon"
HEPNOS_CORES_PER_PE=$(( 32 / $HEPNOS_PES_PER_NODE ))
srun --exclusive -n ${NUM_PES_FOR_HEPNOS} -N ${NUM_NODES_FOR_HEPNOS} ${NODES_FOR_HEPNOS} \
      bedrock ${PROTOCOL} -c ${HEPNOS_CONFIG} -v error &
HEPNOS_PID=$!

echo "Waiting for HEPnOS daemon to start up"
while [ ! -f ${HEPNOS_SSG} ]; do sleep 10; done

if [ "$HEPNOS_LOADER_ENABLE_PROFILING" -eq "1" ]; then
  export MARGO_ENABLE_DIAGNOSTICS=1
  export MARGO_ENABLE_PROFILING=1
else
  export MARGO_ENABLE_DIAGNOSTICS=0
  export MARGO_ENABLE_PROFILING=0
fi

echo "Requesting databases"
timeout ${HEPNOS_UTILITY_TIMEOUT} \
    srun --exclusive -n 1 -N 1 ${NODES_FOR_UTILITY} hepnos-list-databases \
        ${PROTOCOL} -s ${HEPNOS_SSG} > ${DATABASES_CONFIG}
RET=$?
if [ "$RET" -eq "124" ]; then
    echo "ERROR: hepnos-list-databases timed out"
    kill $HEPNOS_PID
    exit -1
fi

LOADER_PRODUCT_ARGS=""
for p in ${HEPNOS_LOADER_PRODUCTS[@]}; do
    LOADER_PRODUCT_ARGS="${LOADER_PRODUCT_ARGS} -n ${p}"
done

echo "Starting dataloader"
echo `pwd`
NUM_PES_FOR_LOADER=$(( $NUM_NODES_FOR_LOADER * $HEPNOS_LOADER_PES_PER_NODE ))
LOADER_CORES_PER_PE=$(( 32 / $HEPNOS_LOADER_PES_PER_NODE ))
start_time=`date +%s`
timeout ${HEPNOS_LOADER_TIMEOUT} \
    srun --exclusive -n ${NUM_PES_FOR_LOADER} -N ${NUM_NODES_FOR_LOADER} \
             ${NODES_FOR_LOADER} hepnos-dataloader \
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
    echo "ERROR: hepnos-dataloader timed out"
    echo "RUNTIME: ${CONST_TIMEOUT}" >> $EXPDIR/dataloader-output.txt
    kill $HEPNOS_PID
    exit -1
fi
if grep -q "ESTIMATED" $EXPDIR/dataloader-output.txt
then
	runtime=$((end_time-start_time))
	echo "RUNTIME: ${runtime}" >> $EXPDIR/dataloader-output.txt
else
    echo "ERROR: hepnos-dataloader failed"
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

    echo "Running PEP benchmark"
    PEP_CORES_PER_PE=$(( 32 / $HEPNOS_PEP_PES_PER_NODE ))
    start_time=`date +%s`
    timeout ${HEPNOS_PEP_TIMEOUT} \
    srun --exclusive -n ${NUM_PES} -N ${NUM_NODES_FOR_PEP} \
              ${NODES_FOR_PEP}  hepnos-pep-benchmark \
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
        echo "ERROR: hepnos-pep timed out"
        echo "TIME: ${CONST_TIMEOUT}" >> $EXPDIR/pep-output.txt
        kill $HEPNOS_PID
        exit -1
    fi
    if grep -q "Benchmark completed" $EXPDIR/pep-output.txt
    then
    	runtime=$((end_time-start_time))
	echo "TIME: ${runtime}" >> $EXPDIR/pep-output.txt
    else
        echo "ERROR: hepnos-pep failed"
        echo "TIME: ${CONST_FAILURE}" >> $EXPDIR/pep-output.txt
        kill $HEPNOS_PID
        exit -1
    fi
fi

echo "Shutting down HEPnOS"
timeout ${HEPNOS_UTILITY_TIMEOUT} \
srun --exclusive -n 1 -N 1 ${NODES_FOR_UTILITY} hepnos-shutdown $PROTOCOL $DATABASES_CONFIG
RET=$?
if [ "$RET" -eq "124" ]; then
    echo "ERROR: hepnos-shutdown timed out"
    kill $HEPNOS_PID
    exit -1
fi
