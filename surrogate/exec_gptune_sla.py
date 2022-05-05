#! /usr/bin/env python

# GPTune Copyright (c) 2019, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S.Dept. of Energy) and the University of
# California, Berkeley.  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Intellectual Property Office at IPO@lbl.gov.
#
# NOTICE. This Software was developed under funding from the U.S. Department
# of Energy and the U.S. Government consequently retains certain rights.
# As such, the U.S. Government has been granted for itself and others acting
# on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in
# the Software to reproduce, distribute copies to the public, prepare
# derivative works, and perform publicly and display publicly, and to permit
# other to do so.
#

"""
Example of invocation of this script:

mpirun -np 1 python exec_gptune_sla.py -ntask 1 -seed 42 -m models/model-4-true-true.pkl -nrun 100 -ninit 10 -run_index 1

"""


################################################################################
import sys
import os
import mpi4py
import logging
sys.path.insert(0, os.path.abspath(__file__ + "/../GPTune/"))
logging.getLogger('matplotlib.font_manager').disabled = True

from autotune.search import *
from autotune.space import *
from autotune.problem import *
from gptune import * # import all
import openturns as ot
import matplotlib.pyplot as plt

import argparse
from mpi4py import MPI
import numpy as np
import time
Time_start = time.time()
print ('time...now', Time_start)
import random

############################################### 
import pickle, glob
import functools
import pathlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
HERE = os.path.dirname(os.path.abspath(__file__))

from black_box_gptune import run

################################################################################

# Define Problem

# YL: for the spaces, the following datatypes are supported:
# Real(lower, upper, transform="normalize", name="yourname")
# Integer(lower, upper, transform="normalize", name="yourname")
# Categoricalnorm(categories, transform="onehot", name="yourname")

# Argmin{x} objectives(t,x), for x in [0., 1.]

def create_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument('-nodes', type=int, default=1,help='Number of machine nodes')
    parser.add_argument('-cores', type=int, default=2,help='Number of cores per machine node')
    parser.add_argument('-machine', type=str,default='-1', help='Name of the computer (not hostname)')
    parser.add_argument('-optimization', type=str,default='GPTune', help='Optimization algorithm (opentuner, hpbandster, GPTune)')
    parser.add_argument('-ntask', type=int, default=1, help='Number of tasks')
    parser.add_argument('-nrun', type=int, default=20, help='Number of runs per task')
    parser.add_argument('-perfmodel', type=int, default=0, help='Whether to use the performance model')
    parser.add_argument('-tvalue', type=float, default=1.0, help='Input task t value')
    parser.add_argument('-tla', type=int, default=0, help='Whether perform TLA after MLA when optimization is GPTune') 
    parser.add_argument('-dsize', type=str,default='s', help='problem size')
    parser.add_argument('-outfolder', type=str,default='s', help='outfolder')
    parser.add_argument('-seed', type=int, default=1234, help='Set seed') 
    parser.add_argument('-run_index', type=int, default=1, help='Run index') 
    parser.add_argument('-ninit', type=int, default=10, help='Set inital configs')
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        required=True,
        help="Model from which to generate random points",
    )
    return parser

def objectives(config: dict):
    scale       = config['scale']
    enable_pep  = config['enable_pep']
    more_params = config['more_params']

    model_path = os.path.join(HERE, f"models/model-{scale}-{str(enable_pep).lower()}-{str(more_params).lower()}.pkl")
    model_file = model_path.split("/")[-1]
    objective = run(config, model_path, maximise=False, with_sleep=False)
    time.sleep(3)
    
    ### save results
    now = time.time()
    elapsed_eval = now - Time_start
    result = pd.DataFrame(data=[config], columns=list(config.keys()))
    result["objective"] = objective
    result["elapsed_sec"] = elapsed_eval
    dir_path = f"exp/gptune/{model_file[:-4]}-{Run_index}"         
    pathlib.Path(dir_path).mkdir(parents=False, exist_ok=True)                          
    try:
        results_cvs = pd.read_csv(dir_path+"/results.csv")
        results_cvs = results_cvs.append(result, ignore_index=True)
    except:    
        results_cvs = result
    results_cvs.to_csv(dir_path+"/results.csv",index=False)
    return [objective]

def cst1(x):
    return x <= 100

def models(point):
    # global test
#     t = point['t']
#     x = point['x']
    return [np.random.uniform()]

def create_gptune(scale_task, enable_pep_task, more_params_task):

    tuning_metadata = {
        "tuning_problem_name": "hepnos", #f"hepnos-{scale_task}-{str(enable_pep_task).lower()}-{str(more_params_task).lower()}-{Run_index}",
        "use_crowd_repo": "no",
        "machine_configuration": {
            "machine_name": "swing",
            "amd": { "nodes": 1, "cores": 128 }
        },
        "software_configuration": {},
        "loadable_machine_configurations": {},
        "loadable_software_configurations": {}
    }  
    
    (machine, processor, nodes, cores) = GetMachineConfiguration(meta_dict = tuning_metadata)
    print ("machine: " + machine + " processor: " + processor + " num_nodes: " + str(nodes) + " num_cores: " + str(cores))
    os.environ['MACHINE_NAME'] = machine
    os.environ['TUNER_NAME'] = TUNER_NAME

    ## input space 
    scale       = Integer(1, 16, transform="normalize", name="scale")
    enable_pep  = Categoricalnorm([True, False], transform="onehot", name="enable_pep")
    more_params = Categoricalnorm([True, False], transform="onehot", name="more_params")
    
    ## param space     
    p0 = Categoricalnorm([True, False], transform="onehot", name="busy_spin")
    p1 = Integer(1, 16, transform="normalize", name="hepnos_num_event_databases")    
    p2 = Integer(1, 16, transform="normalize", name="hepnos_num_product_databases")
    p3 = Integer(1, 32, transform="normalize", name="hepnos_num_providers")    
    p4 = Integer(0, 63, transform="normalize", name="hepnos_num_rpc_threads") 
    p5 = Categoricalnorm([1, 2, 4, 8, 16, 32], transform="onehot", name="hepnos_pes_per_node")     
    p6 = Categoricalnorm(['fifo','fifo_wait'], transform="onehot", name="hepnos_pool_type")     
    p7 = Categoricalnorm([True, False], transform="onehot", name="hepnos_progress_thread") 
    p8 = Integer(1, 2048, transform="normalize", name="loader_batch_size")     
    p9 = Categoricalnorm([1, 2, 4, 8, 16], transform="onehot", name="loader_pes_per_node") 
    p10 = Categoricalnorm([True, False], transform="onehot", name="loader_progress_thread")     
    Tuning_params = [p0, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]
    
    if more_params_task:
#         print ('.....include more params...')
        p11 = Categoricalnorm([True, False], transform="onehot", name="loader_async") 
        p12 = Integer(1, 63, transform="normalize", name="loader_async_threads")   
        Tuning_params.extend([p11, p12])
    if enable_pep_task: 
#         print ('.....include enable_pep...')
        p13 = Categoricalnorm([True, False], transform="onehot", name="pep_progress_thread") 
        p14 = Integer(1, 31, transform="normalize", name="pep_num_threads")
        p15 = Integer(8, 1024, transform="normalize", name="pep_ibatch_size")
        p16 = Integer(8, 1024, transform="normalize", name="pep_obatch_size")
        p17 = Categoricalnorm([1, 2, 4, 8, 16, 32], transform="onehot", name="pep_pes_per_node") 
        p18 = Categoricalnorm([True, False], transform="onehot", name="pep_no_preloading") 
        p19 = Categoricalnorm([True, False], transform="onehot", name="pep_no_rdma") 
        Tuning_params.extend([p13, p14, p15, p16, p17, p18, p19])
    
    ## output space    
    y = Real(float("-Inf"), float("Inf"), name="y")

    IS = Space([scale, enable_pep, more_params])
    PS = Space(Tuning_params)
    OS = Space([y])

    constraints = {} #{"cst1": "x >= 1 and x <= 100"}    
    
    problem  = TuningProblem(IS, PS, OS, objectives, constraints, None)  # no performance model  
    # historydb = HistoryDB(meta_dict=tuning_metadata)
    '''
    suppose your has M compute nodes, m cores per node, and each run requires N nodes, then you need to set:
    options['distributed_memory_parallelism']=False
    options['shared_memory_parallelism'] = True
    options['objective_evaluation_parallelism']=True
    options['objective_multisample_threads']=M/N
    options['objective_nospawn']=True
    options['objective_nprocmax']=N*m
    
    M compute nodes 
    each has m cores 
    each batch runs K evaluations, each requires c cores
    options['objective_multisample_processes'] = K
    options['objective_nprocmax'] = c
    then makes sure in .gptune/meta.json that 
          "nodes": M+1,
          "cores": m
    and makes sure that K*c<=M*m when you set K. 
    M = 1 
    m = 128 
    N = 1
    K evaluations, each requires c cores 
    k*c <= M*m
    '''
    ## parallel 
#     computer = Computer(nodes=nodes, cores=cores, hosts=None) 
#     options  = Options()
#     options['model_restarts'] = 1
#     options['distributed_memory_parallelism'] = True ######## False
#     options['shared_memory_parallelism'] = True
#     options['objective_evaluation_parallelism'] = True ######## False
#     options['objective_multisample_threads'] = 1    ### M/N  
#     options['objective_multisample_processes'] = 10 ### k ## maximum number of function evaluations running in parallel
#     options['objective_nprocmax'] = 1          ### c, N*m ### number of cores per function evaluation
    
#     options['model_processes'] = 1
#     options['search_multitask_processes'] = 1  #########
#     options['model_class'] = 'Model_GPy_LCM' #'Model_GPy_LCM'
#     options['verbose'] = False #False
#     options['sample_class'] = 'SampleOpenTURNS'#'SampleLHSMDU'
#     options.validate(computer=computer)
    
#     ## serial 
    problem  = TuningProblem(IS, PS, OS, objectives, constraints, None)  # no performance model  
    # historydb = HistoryDB(meta_dict=tuning_metadata)
    computer = Computer(nodes=nodes, cores=cores, hosts=None) 
    options  = Options()
    options['model_restarts'] = 1
    options['distributed_memory_parallelism'] = False
    options['shared_memory_parallelism'] = False
    options['objective_evaluation_parallelism'] = False
    options['objective_multisample_threads'] = 1
    options['objective_multisample_processes'] = 1
    options['objective_nprocmax'] = 1
    options['model_processes'] = 1
    options['model_class'] = 'Model_GPy_LCM' #'Model_GPy_LCM'
    options['verbose'] = True #False
    options['sample_class'] = 'SampleOpenTURNS'#'SampleLHSMDU'
    options.validate(computer=computer)    
    
    return problem, computer, options

if __name__ == "__main__":
    
    global nodes
    global cores
    global Run_index

    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()
    ntask = args.ntask
    nrun = args.nrun
    tvalue = args.tvalue
    TUNER_NAME = args.optimization
    perfmodel = args.perfmodel
    tla = args.tla
    DSIZE = args.dsize
    SEED  = args.seed
    NINIT = args.ninit
    Run_index = args.run_index
    ot.RandomGenerator.SetSeed(int(SEED))
    
    model_file = args.model.split("/")[-1]
    scale, enable_pep, more_params = model_file[:-4].split("-")[1:4]
    scale, enable_pep, more_params = int(scale), enable_pep == "true", more_params == "true"    
    
    problem, computer, options = create_gptune(scale, enable_pep, more_params)

    if ntask == 1:
        giventask =  [[scale, enable_pep, more_params]] #[[input_sizes[DSIZE][0]]]
        print ('problem size is', DSIZE, giventask)
    elif ntask == 2:
        giventask = [[scale, enable_pep, more_params], [scale, enable_pep, more_params]] #[[input_sizes[DSIZE][0]]]
    else:
        giventask = [[round(tvalue*float(i+1),1)] for i in range(ntask)]

    NI=len(giventask)  ## number of tasks
    NS=nrun ## number of runs 
    TUNER_NAME = os.environ['TUNER_NAME']

    if(TUNER_NAME=='GPTune'):
        data = Data(problem)
        ## add inital points
        data.I = giventask 
        init_file = os.path.join(HERE, "data", f"exp-DUMMY-{model_file[6:-4]}-{Run_index}.csv")
        init_df = pd.read_csv(init_file).drop(columns="job_id,objective,timestamp_submit,timestamp_gather,timestamp_start,timestamp_end,dequed".split(","))
        init_df = init_df.iloc[:NINIT]
        initial_points = []
        for idx, row in init_df.iterrows():
            point = [] 
            for i in range(len(problem.parameter_space)):
                point.append(row[problem.parameter_space[i].name])
            initial_points.append(point)
        data.P = [initial_points]
        
        ## create and run gptune 
        gt = GPTune(problem, computer=computer, data=data,options=options,driverabspath=os.path.abspath(__file__))
        (data, modeler, stats) = gt.MLA(NS=NS, Igiven=giventask, NI=NI, NS1=NINIT)#int(max(NS//2, 1)))
        print("stats: ", stats)
        """ Print all input and parameter samples """
        for tid in range(NI):
            print("tid: %d" % (tid))
            print("    t:%f " % (data.I[tid][0]))
            print("    Ps ", data.P[tid])
            print("    Os ", data.O[tid].tolist())
            print('    Popt ', data.P[tid][np.argmin(data.O[tid])], 'Oopt ', min(data.O[tid])[0], 'nth ', np.argmin(data.O[tid]))
            
        if(tla==1):
            """ Call TLA for 2 new tasks using the constructed LCM model"""
            
            (aprxopts, objval, stats) = gt.TLA1(newtask, NS=None)
            print("stats: ", stats)

            """ Print the optimal parameters and function evaluations"""
            for tid in range(len(newtask)):
                print("new task: %s" % (newtask[tid]))
                print('    predicted Popt: ', aprxopts[tid], ' objval: ', objval[tid]) 
