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
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 3 
mv gptune.db/* ./exp/gptune/model-4-true-true-3/
################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 4 
mv gptune.db/* ./exp/gptune/model-4-true-true-4/
################################# RUN
rm -rf gptune.db
# mv ./model-4-true-true-1/results.csv /model-4-true-true-1/results.csv
mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 5 
mv gptune.db/* ./exp/gptune/model-4-true-true-5/

################################# RUN
# rm -rf gptune.db
# mkdir ./results/
# rm ./results/results_4tt.csv
# mpirun -np 1 python exec_gptune_sla_4tt.py -nrun 512 -ntask 1 -perfmodel 0 -optimization GPTune
# mkdir ./exp/gptune/TLA_experiments/SLA-GPTune-4tt/
# mv gptune.db/hepnos.json ./TLA_experiments/SLA-GPTune-4tt/

################################ RUN SLA for small 
# cd /gpfs/jlse-fs0/users/jkoo/code/gptune/examples/RSBench_exp/rsbench_gptune_dtla_s
# rm -rf gptune.db
# python demo_sla.py -nrun 200 -ntask 1 -perfmodel 0 -optimization GPTune -dsize s 
# mv gptune.db/rsbench.json ./TLA_experiments/SLA-GPTune-s-200/
# mv save_results.npy save_results_sla_s_rsbench.npy

################################ RUN SLA for medium 
# cd /gpfs/jlse-fs0/users/jkoo/code/gptune/examples/RSBench_exp/rsbench_gptune_dtla_m
# rm -rf gptune.db
# python demo_sla.py -nrun 200 -ntask 1 -perfmodel 0 -optimization GPTune -dsize m 
# mv gptune.db/rsbench.json ./TLA_experiments/SLA-GPTune-m-200/
# mv save_results.npy save_results_sla_m_rsbench.npy

################################ RUN SLA for large 
# cd /gpfs/jlse-fs0/users/jkoo/code/gptune/examples/RSBench_exp/rsbench_gptune_dtla_l
# rm -rf gptune.db
# python demo_sla.py -nrun 200 -ntask 1 -perfmodel 0 -optimization GPTune -dsize l
# mv gptune.db/rsbench.json ./TLA_experiments/SLA-GPTune-l-200/
# mv save_results.npy save_results_sla_l_rsbench.npy

################################# RUN DTLA on sm 
# cd /gpfs/jlse-fs0/users/jkoo/code/gptune/examples/RSBench_exp/rsbench_gptune_dtla_sm
# rm -rf gptune.db
# python merge.py
# mkdir -p gptune.db
# mv db.out gptune.db/rsbench.json
# python demo_dtla.py -nrun 200 -ntask 4 -perfmodel 0 -optimization GPTune -dsize sm
# mv gptune.db/rsbench.json ./TLA_experiments/DTLA-GPTune-sm-200/
# mv save_results.npy save_results_dtla_sm_rsbench.npy

# ################################# RUN DTLA on ml
# # cd /gpfs/jlse-fs0/users/jkoo/code/gptune/examples/RSBench_exp/rsbench_gptune_dtla_sm
# rm -rf gptune.db
# python merge.py
# mkdir -p gptune.db
# mv db.out gptune.db/rsbench.json
# python demo_dtla.py -nrun 200 -ntask 4 -perfmodel 0 -optimization GPTune -dsize ml
# mv gptune.db/rsbench.json ./TLA_experiments/DTLA-GPTune-ml-200/
# mv save_results.npy save_results_dtla_ml_rsbench.npy

# ################################# RUN DTLA on xl 
# # cd /gpfs/jlse-fs0/users/jkoo/code/gptune/examples/RSBench_exp/rsbench_gptune_dtla_sm
# rm -rf gptune.db
# python merge.py
# mkdir -p gptune.db
# mv db.out gptune.db/rsbench.json
# python demo_dtla.py -nrun 200 -ntask 4 -perfmodel 0 -optimization GPTune -dsize xl
# mv gptune.db/rsbench.json ./TLA_experiments/DTLA-GPTune-xl-200/
# mv save_results.npy save_results_dtla_xl_rsbench.npy

















