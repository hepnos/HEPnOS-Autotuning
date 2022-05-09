
import numpy as np
import sys
from bayesian import ParamProbability as ParamProbability
from sklearn.model_selection import train_test_split
from dataset_info import DatasetInfo
import pandas as pd

def objective_fn(param, X_tgt, y_tgt):
  idx=list(zip(*np.where((X_tgt == param).all(axis=1))))
  #idx=list(zip(*np.where((X_tgt.values.astype(int) == param).all(axis=1))))
  if idx is None:
    print('Error idx does not exist: ', idx)
  best_loss = y_tgt[idx[0]]
#     display('Trial loss : {} param: {}'.format(best_loss, param))
  return best_loss


"""
The selection algorithm selects the best candidate with the 
highest expected improvement metric.
"""
def selection(X_src, X_tgt, y_tgt, x_obs, y_obs, param_prob, gamma):

    #print (np.shape(X_src),np.shape(X_tgt),np.shape(y_tgt),np.shape(x_obs),np.shape(y_obs) )
    # Construct probability for each parameter
    for label_idx, datalabel in enumerate(X_src.columns):
        xk = np.unique(X_src[datalabel].values).astype(int)
        param_prob[label_idx].update_probability(datalabel, xk, x_obs[:, label_idx], y_obs, best_ratio=gamma)

    max_EI = 0.0
    
    expected_improvement = np.empty(len(X_tgt))
    lx = np.ones(len(X_tgt))
    gx = np.ones(len(X_tgt))

    for label_idx, datalabel in enumerate(X_tgt.columns):
        a = X_tgt[datalabel].values
        lx *= param_prob[label_idx].best_yk[a.astype(int)]#[a.astype(int)-1]
        gx *= param_prob[label_idx].worst_yk[a.astype(int)]
        
    expected_improvement = 1 / (gamma + (gx/lx) * (1-gamma))
    max_idx = np.argmax(expected_improvement)
    max_EI = expected_improvement[max_idx]
    max_param = X_tgt.values[max_idx].astype(int)
    
    y_ei_sorted_index = np.argsort(-expected_improvement)
    y_selected=y_tgt[y_ei_sorted_index][0:500]
    
    for ei_idx in y_ei_sorted_index:
        param = X_tgt.values[ei_idx].astype(int)
        if len(x_obs[(x_obs == param).all(axis=1)]) <= 0:
            max_EI = expected_improvement[ei_idx]
            max_param = param
            break
    
#     print('Best candidate EI: {0} param: {1}'.format(max_EI, max_param))
    return max_param

def run_bayesian_selection(X_src, X_tgt, y_src, y_tgt, sample_size, thresholds, abs_count, seed, gamma) :
    recall_list = {}

    # Choose the number of samplels from the Src dataset
    train_size = int(0.99*len(X_src))
    print('Number of samples from the Src dataset: ', train_size)
    train_ids, test_ids = train_test_split(range(X_src.shape[0]), test_size=len(X_src)-train_size, random_state=seed)
    x_train = X_src.iloc[train_ids].values
    y_train = y_src[train_ids]

    param_prob = []
    # Construct the p_good and p_bad using the Src dataset
    for label_idx, datalabel in enumerate(X_src.columns):
        xk = np.unique(X_src[datalabel].values).astype(int)

        prob = ParamProbability(use_prior=True)
        #print (datalabel, np.shape(xk),np.shape(x_train[:, label_idx].astype(int)),np.shape(y_train[:,0]))
        prob.prior_probability(datalabel, xk, x_train[:, label_idx].astype(int), y_train[:,0], best_ratio=gamma)
        param_prob.append(prob)

    # Choose the number of samples from the Tgt dataset
    train_size = 10 #20
    train_ids, test_ids = train_test_split(range(X_tgt.shape[0]), test_size=len(X_tgt)-train_size, random_state=seed)
    x_obs = X_tgt.iloc[train_ids].values
    y_obs = y_tgt[train_ids]

    # construct trials
    trials = []
    trials_loss = []
    x_obs_int = x_obs.astype(int)

    trials = x_obs_int[:]
    trials_loss = y_obs[:]

    # Iteratively select one sample at a time to add to the list of observation
    # based on the prediction from surrogate model.
    # Evaluate the true objective function of the selected candidate.
    # Add the candidate to the history of observation which will be used to
    # update the surrogate model.
    print ("sample_size-train_size",sample_size-train_size)
    for it in range(sample_size-train_size):
        #print ("it",it)
        trial=selection(X_src, X_tgt, y_tgt, trials, trials_loss.flatten(), param_prob, gamma)
        trials = np.vstack([trials, trial])

        loss=objective_fn(trial, X_tgt, y_tgt)
        trials_loss = np.append(trials_loss,loss)

    best_loss = np.amin(trials_loss)
    c_idx = 0
    # For each threshold, calculate the recall score, which gives the fraction
    # of good configurations that are present in tthe model's selected list.
    for threshold in thresholds:
        good_configs = trials_loss[np.where(trials_loss < threshold)]
        recall_val = np.count_nonzero(good_configs) / float(abs_count[c_idx])
        #print ("recall_list", recall_list)
        #print ("threshold", threshold)
        #print ("recall_val",recall_val)
        recall_list[threshold[0]] = recall_val
        c_idx += 1
        print('threshold : ', threshold, ' configs: ', good_configs, ' recall_val: ', recall_val)

    return best_loss, recall_list, trials, trials_loss

def main():
  args = sys.argv[1:]
  if len(args) == 0:
    sys.exit("Enter the dataset name")

  dName = args[0] 
  print('-------------------')
  print('Evaluating transfer learning ', dName)
  ds = DatasetInfo(dName)
  ds.initialize_dataset_tl_DH()
  #ds.initialize_dataset_tl()

  # Each sample size is evaluated numSeeds times to get the mean and std
  numSeeds = 5 #10 #desired value for runs 10
  seedList = np.random.choice(100,numSeeds,replace=False)
  
  # Get the best application performance
  idx_min = np.argmin(ds.y_new_bin)
  print('Exhaustive best: ', ds.y_new_bin[idx_min])

  # Set the error threshold below which is considered a good configuration
  # Obtain the recall score (howmany of the good configurations were selected)
  # for each of these error thersholds.
  if dName == 'HYPRE':
      perc_optimal = [0.05, 0.1, 0.17644641442, 0.23691549007]
  elif dName == 'KRIPKE.L0':
      perc_optimal = [0.05, 0.1, 0.15, 0.20]
  # how do we set this?
  elif dName == 'DH_surrogate':
      perc_optimal = [0.05, 0.1, 0.15, 0.20]
  
  thresholds = []
  abs_counts = []
  idx_min_inv = np.argmin(ds.y_new_bin)
  best_loss_list = np.zeros(numSeeds)
  
  
  for percent in perc_optimal:
      threshold_good = (1 + percent) * ds.y_new_bin[idx_min]
      thresholds.append(threshold_good)
      good_configs = np.where(ds.y_new_bin <= threshold_good)
      abs_counts.append(np.count_nonzero(good_configs))
  
  # Number of good configurations
  print('Thresholds: ', thresholds)
  print('Good configuration counts: ', abs_counts)
  
  dataset_len = len(ds.X_bin_u)
  # For the paper, we used the same sample size as used by PerfNet. Here we use
  # 1% of the total samples in D_tgt + 100
  sample_size = [100] #[int(0.01*dataset_len)+100]

  print (sample_size)
  feats = ds.X_bin_feat_sel
  feats.append("objective")  
  for size in sample_size:
      s_order = 0
      for seed in seedList:
          best_loss, recall_list,trials,trials_loss = run_bayesian_selection(
              ds.X_small_bin_u, ds.X_bin_u, ds.y_new_small_bin, ds.y_new_bin,
              size, thresholds, abs_counts, seed, gamma=0.01)
          best_loss_list = np.append(best_loss_list, best_loss)
          print('Sample size: {0} Best loss: {1}'.format(size, best_loss))
          print('Recall: {0} Recall: {1}'.format(size, recall_list))
          s_order = s_order+1
          if (size == sample_size[-1]):
                T1 = np.concatenate((trials,trials_loss.reshape(-1,1)), axis=1)
                df = pd.DataFrame(data=T1, columns=feats)
                df.to_csv('trials_{}.csv'.format(s_order),sep=',')   
  
if __name__ == "__main__":
    main()

