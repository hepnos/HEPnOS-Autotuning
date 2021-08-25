#!/bin/bash
#SBATCH -N 4
#SBATCH --time=30:00
#SBATCH -p bdwall

set -eu
CONFIGFILE=config.yaml
CONNECTIONFILE=connection.yaml
cd $EXPDIR

rm -f ${CONNECTIONFILE}

source settings.sh

export PSM2_MULTI_EP=1
export FI_PSM2_DISCONNECT=1

echo "Setting up spack and modules"
source $SCRIPTDIR/../spack/share/spack/setup-env.sh

echo "Activating env"
module load gcc/8.2.0-g7hppkz
module load intel-mpi/2018.4.274-ozfo327
spack env activate hepnos
spack load -r hepnos@master
spack load -r hepnos-dataloader@master

echo "Starting up HEPnOS daemon"
srun -N 2 -n 4 --exclusive hepnos-daemon $CONFIGFILE $CONNECTIONFILE &
echo "Waiting for HEPnOS daemon to start up"
while [ ! -f ${CONNECTIONFILE} ]; do sleep 10; done
echo "Starting dataloader"
echo `pwd`
(time srun -N 2 -n 2 --exclusive hepnos-dataloader \
             -c ${CONNECTIONFILE} \
             -i ${HEPNOS_DATASET} \
             -o Nova \
             -l xxx \
             -b ${HEPNOS_CLIENT_BATCH_SIZE} ${HEPNOS_CLIENT_USE_PROGRESS_THREAD} \
             -v info ) \
    &> output.txt

sleep 5
echo "Shutting down HEPnOS"
srun -n 1 -N 1 --exclusive hepnos-shutdown $CONNECTIONFILE
