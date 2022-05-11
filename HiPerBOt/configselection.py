import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

import sys
import matplotlib.pyplot as plt
from timeit import default_timer as timer
import networkx as nx
# import GraphConstruct as gc 
import scipy as sc
from scipy import stats
from sklearn.preprocessing import minmax_scale
from scipy import sparse
import multiprocessing as mp
from functools import partial
import shutil, os
from Utilities import Utilities as utils
import matplotlib as matplotlib
from bayesian import ParamProbability as ParamProbability
from sklearn.model_selection import train_test_split
from timeit import default_timer as timer
import time



from dataset_info import DatasetInfo

def objective_fn(param, X_bin_u, y_new_bin):
  idx=list(zip(*np.where((X_bin_u.values.astype(int) == param).all(axis=1))))
  if idx is None:
    print('Error idx does not exist: ', idx)
  best_loss = y_new_bin[idx[0]]
#     display('Trial loss : {} param: {}'.format(best_loss, param))
  return best_loss

def selection(X_bin_u, y_new_bin, x_obs, y_obs, param_prob, gamma):
    # Construct probability for each parameter
#     param_prob = {}
    for label_idx, datalabel in enumerate(X_bin_u.columns):
        xk = np.unique(X_bin_u[datalabel].values).astype(int)
        param_prob[label_idx].update_probability(datalabel, xk, x_obs[:, label_idx], y_obs, best_ratio=gamma)

    max_EI = 0.0

    expected_improvement = np.empty(len(X_bin_u))
    lx = np.ones(len(X_bin_u))
    gx = np.ones(len(X_bin_u))

    for label_idx, datalabel in enumerate(X_bin_u.columns):
        a = X_bin_u[datalabel].values
        lx *= param_prob[label_idx].best_yk[a.astype(int)]#[a.astype(int)-1]
        gx *= param_prob[label_idx].worst_yk[a.astype(int)]

    expected_improvement = 1 / (gamma + (gx/lx) * (1-gamma))
    max_idx = np.argmax(expected_improvement)
    max_EI = expected_improvement[max_idx]
    max_param = X_bin_u.values[max_idx].astype(int)

    y_ei_sorted_index = np.argsort(-expected_improvement)
    y_selected=y_new_bin[y_ei_sorted_index][0:500]

    # if the configs in x_obs are not in X_bin_u, use the config with max expectation as max_param
    for ei_idx in y_ei_sorted_index:
        param = X_bin_u.values[ei_idx].astype(int)
        if len(x_obs[(x_obs == param).all(axis=1)]) <= 0:
            max_EI = expected_improvement[ei_idx]
            max_param = param
            break

#     display('Best candidate EI: {} param: {}'.format(max_EI, max_param))
    return max_param

def run_bayesian_selection(X_bin_u, y_new_bin,X_bin_u_init, y_new_bin_init, sample_size, train_size, seed, s_order, gamma, threshold_good) :
    recall_list = {}

    if (sample_size == 139):
        start = timer()
    param_prob = []
    for label_idx, datalabel in enumerate(X_bin_u.columns):
        prob = ParamProbability(use_prior=False)
        param_prob.append(prob)


    train_ids, test_ids = train_test_split(range(X_bin_u.shape[0]), test_size=len(X_bin_u)-train_size, random_state=seed)
    #print ("seed",seed,"train_ids", train_ids)
    x_obs = X_bin_u_init.iloc[s_order*10:(s_order+1)*10].values #X_bin_u.iloc[train_ids].values
    y_obs = y_new_bin_init[s_order*10:(s_order+1)*10]
    #print('min training ', np.min(y_obs), len(y_obs))


    # construct trials
    trials = []
    trials_loss = []
    x_obs_int = x_obs.astype(int)

    trials = x_obs_int[:]
    trials_loss = y_obs[:]
    #print('Trials : ', (sample_size-train_size))

    if (sample_size-train_size) < 0:
        print('Sample size {0} less than train size {1}'.format(sample_size, train_size))
        assert(False)
    #eval_time_avg = []
    for it in range(sample_size-train_size):
        #before_sel = time.time()
        trial=selection(X_bin_u, y_new_bin, trials, trials_loss, param_prob, gamma)
        #after_sel = time.time()
        #eval_time = after_sel - before_sel
        #eval_time_avg.append(eval_time)
        trials = np.vstack([trials, trial])
        loss=objective_fn(trial, X_bin_u, y_new_bin)
        trials_loss = np.append(trials_loss,loss)
        
    #print ("eval_time",np.mean(eval_time_avg))
    best_loss = np.amin(trials_loss)
    num_good = (trials_loss < threshold_good).sum()
    pc_score_g = stats.percentileofscore(trials_loss,threshold_good)

    return best_loss, pc_score_g, num_good, trials, trials_loss

def main():
  args = sys.argv[1:]
  if len(args) == 0:
    sys.exit("Enter the dataset name")

  dName = args[0] 
  print('-------------------')
  print('Evaluating ', dName)
  ds = DatasetInfo(dName)
  ds.initialize_dataset()


  numSeeds = 5 #10 #50 #10 Uncomment for sensitivity #desired value for runs 10
  seedList = np.random.choice(100,numSeeds,replace=False)
  
  idx_min = np.argmin(ds.y_new_bin)
  print('Exhaustive best: ', ds.y_new_bin[idx_min])
  #print('Exhaustive best configuration: ', ds.X_bin_u.iloc[idx_min])
  dataset_len = len(ds.X_bin_u)
  init_size = 10 #int((1-ds.test_size)*dataset_len)
  #act_init_size = 1-(float(init_size - 50)/dataset_len)
  print('dataset len ', dataset_len,init_size)
  
  
  #init_size = 250 # Uncomment for sensitivity
  sample_size = np.zeros(ds.nIter, dtype=int) # Uncomment for sensitivity
  for i in range(ds.nIter):
      sample_size[i] = init_size + (i)*ds.to_add
      #print('sample_size', i, sample_size[i])
  
  metric_mean = {}
  metric_std = {}
  metric_mean_list = []
  metric_std_list = []
  best_loss_all = []
  pc_g_all = []
  num_good_all = []
  trials_all = np.zeros((1,20))

  #print(ds.X_new_bin.columns)
  #print(len(sample_size), sample_size)
  threshold_good = np.percentile(ds.y_bin,ds.perc_optimal)
  feats = ds.X_bin_feat_sel
  feats.append("objective")
  start = time.time()
  for size in sample_size:
      #print('Sample size: ', size)
      best_loss_list = []
      pc_g_list = []
      num_good_list = []
      s_order = 0
      for seed in seedList:
          before_run = time.time()
          best_loss, pc_score_g, num_good, trials,trials_loss = run_bayesian_selection(ds.X_bin_u, ds.y_new_bin,ds.X_bin_u_init, ds.y_new_bin_init, size, ds.train_size, seed, s_order=s_order, gamma=ds.gamma_perc, threshold_good=threshold_good)
          best_loss_list = np.append(best_loss_list, best_loss)
          pc_g_list = np.append(pc_g_list, pc_score_g)
          num_good_list = np.append(num_good_list, num_good)

          
          #print('Best loss: ', best_loss)
          #print('Good percentile: ', pc_score_g)
          #print('Num good: ', num_good)
          s_order = s_order+1
          if (size == sample_size[-1]):
                T1 = np.concatenate((trials,trials_loss.reshape(-1,1)), axis=1)
                df = pd.DataFrame(data=T1, columns=feats)
                df.to_csv('trials_{}.csv'.format(s_order),sep=',')

      metric_mean[size] = np.mean(best_loss_list)
      metric_std[size] = np.std(best_loss_list)
      best_loss_all.append(best_loss_list)
      pc_g_all.append(pc_g_list)
      num_good_all.append(num_good_list)
      metric_mean_list.append(metric_mean[size])
      metric_std_list.append(metric_std[size])
      print('sample size: {0} best configuration: {1} std: {2}'.format(size, metric_mean[size], metric_std[size]))
      #print (metric_mean)
      np.savetxt('metric_mean.csv', np.array(metric_mean_list), delimiter=',')
      np.savetxt('metric_std.csv', np.array(metric_std_list), delimiter=',')
      np.savetxt('best_loss_all.csv', np.array(best_loss_all), delimiter=',')
      np.savetxt('pc_g_all.csv', np.array(pc_g_all), delimiter=',')
      np.savetxt('num_good_all.csv', np.array(num_good_all), delimiter=',')
      #np.savetxt('trials.csv', np.array(trials_all), delimiter=',')
    

if __name__ == "__main__":
    main()

