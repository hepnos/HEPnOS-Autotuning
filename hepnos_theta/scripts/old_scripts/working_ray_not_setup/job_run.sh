#!/bin/bash
# Activate env or conda env if applicable:
source activate /lus/theta-fs0/projects/OptADDN/hepnos/sw/dh-env-2
cd exp/
mkdir exp_run
cd exp_run
deephyper hps ambs --evaluator ray --problem hps_1.hepnos.problem.Problem --run hps_1.hepnos.model_run.run --num-workers 32 --n-jobs 32