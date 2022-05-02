#!/bin/bash
#SBATCH --job-name=1_gptune
#SBATCH --account=perfopt
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --output=stdout_sla_4tt_run1.%j

# module load gcc/9.2.0-r4tyw54
# module load nvhpc/21.5-oxhtyof
source activate /home/jkoo/.conda/envs/gptune/
cd ~/spack
. share/spack/setup-env.sh 
spack load gptune
cd /lcrc/project/perfopt/jkoo/code/HEPnOS-Autotuning/surrogate
################################# RUN
# rm -rf gptune.db
# # mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
# mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 1 
# mv gptune.db/* ./exp/gptune/model-4-true-true-1/
# ################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 2 
mv gptune.db/* ./exp/gptune/model-4-true-true-2/
################################# RUN
# rm -rf gptune.db
# # mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
# mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 3 
# mv gptune.db/* ./exp/gptune/model-4-true-true-3/
# ################################# RUN
# rm -rf gptune.db
# # mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
# mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 4 
# mv gptune.db/* ./exp/gptune/model-4-true-true-4/
# ################################# RUN
# rm -rf gptune.db
# # mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
# mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 5 
# mv gptune.db/* ./exp/gptune/model-4-true-true-5/

################################################################## 4 False False
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-false-false.pkl -nrun 100 -ninit 10 -run_index 1 
mv gptune.db/* ./exp/gptune/model-4-false-false-1/
# ################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-false-false.pkl -nrun 100 -ninit 10 -run_index 2 
mv gptune.db/* ./exp/gptune/model-4-false-false-2/
################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-false-false.pkl -nrun 100 -ninit 10 -run_index 3 
mv gptune.db/* ./exp/gptune/model-4-false-false-3/
################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-false-false.pkl -nrun 100 -ninit 10 -run_index 4 
mv gptune.db/* ./exp/gptune/model-4-false-false-4/
################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-false-false.pkl -nrun 100 -ninit 10 -run_index 5 
mv gptune.db/* ./exp/gptune/model-4-false-false-5/















