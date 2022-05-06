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
    parser.add_argument(
        "-m_tl",
        "--model_tl",
        type=str,
        default=None,
        required=True,
        help="TL model",
    )
    return parser

def objectives(config: dict):
    scale       = config['scale']
    enable_pep  = config['enable_pep']
    more_params = config['more_params']
    
    ## new task:
    if scale == 8 and enable_pep == True and more_params == True:
        model_path = os.path.join(HERE, f"models/model-{scale}-{str(enable_pep).lower()}-{str(more_params).lower()}.pkl")
        model_file = model_path.split("/")[-1]
        objective = run(config, model_path, maximise=False, with_sleep=False)
    ## old task:
    if scale == 4 and enable_pep == False and more_params == False:    
        print (".....................Task: ", config['t'])
        print (".....................point",config)      
        objective = model_functions[[scale,enable_pep,more_params]](config)    
        print (".....................model ret: ", ret) 
    
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
        "loadable_machine_configurations": {
            "swing": {
                "amd": {
                    "nodes": 1,
                    "cores": 128
                }
            }
        },
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
    historydb = HistoryDB(meta_dict=tuning_metadata)
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
    options['verbose'] = False #False
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
    
    model_file_tl = args.model_tl.split("/")[-1]
    scale_tl, enable_pep_tl, more_params_tl = model_file_tl[:-4].split("-")[1:4]
    scale_tl, enable_pep_tl, more_params_tl = int(scale_tl), enable_pep_tl == "true", more_params_tl == "true"      
    
    problem, computer, options = create_gptune(scale, enable_pep, more_params)

    if ntask == 1:
        giventask =  [[scale, enable_pep, more_params]] #[[input_sizes[DSIZE][0]]]
        print ('problem size is', DSIZE, giventask)
    elif ntask == 2:
        giventask = [[scale, enable_pep, more_params], [scale_tl, enable_pep_tl, more_params_tl]] #[[input_sizes[DSIZE][0]]]
    else:
        giventask = [[round(tvalue*float(i+1),1)] for i in range(ntask)]

    ### tl model    
    model_functions = {}
    for i in range(1,len(giventask),1):     
        meta_dict = {
            "tuning_problem_name":"hepnos",
            "modeler":"Model_GPy_LCM",
            "task_parameter":[[tvalue_]],
            "input_space": [
                {"name":"scale","type":"int","transformer":"normalize","lower_bound":1,"upper_bound":2100000000},
                {"name":"scale","type":"int","transformer":"normalize","lower_bound":1,"upper_bound":2100000000},
                {"name":"scale","type":"int","transformer":"normalize","lower_bound":1,"upper_bound":2100000000}
            ],
            "parameter_space": [
        {"name": "p0","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p1","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p2","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p3","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p4","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p5","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p6","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p7","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p8","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p9","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p10","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p11","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p12","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p13","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p14","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p15","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p16","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p17","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p18","transformer": "onehot","type": "categorical","categories": []},
        {"name": "p19","transformer": "onehot","type": "categorical","categories": []},
      ],
            "output_space": [{"name":"y","type":"real","transformer":"identity","lower_bound":float('-Inf'),"upper_bound":float('Inf')}],
            "loadable_machine_configurations":{"mymachine":{"myprocessor":{"nodes":[1],"cores":128}}},
            "loadable_software_configurations":{}
        }         
        
        f = open(f"exp/gptune/{model_file_tl[:-4]}-{Run_index}/hepnos.json")
        func_evals = json.load(f)
        f.close()
        model_functions[giventask[i]] = BuildSurrogateModel(metadata_path=None,metadata=meta_dict,function_evaluations=func_evals['func_eval'])        
        
    NI=len(giventask)  ## number of tasks
    NS=nrun ## number of runs 
    TUNER_NAME = os.environ['TUNER_NAME']

    if(TUNER_NAME=='GPTune'):
        data = Data(problem)
        ## add inital points
        data.I = giventask[0] 
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
