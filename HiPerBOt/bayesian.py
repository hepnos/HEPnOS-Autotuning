from __future__ import division
import pandas as pd
import numpy as np
from scipy import stats

_default_prior_weight = 1
_default_prior_prob_weight = 10

class ParamProbability:
    def __init__(self, use_prior=False, prior_weights=_default_prior_weight):
        self.xk = []
        self.best_prior_counts = []
        self.worst_prior_counts = []
        self.best_yk = []
        self.worst_yk = []
        self.use_prior = use_prior
        self.prior_weights = prior_weights
        
    def prior_probability(self, param_name, xk,  x_obs_prior, y_obs_prior, best_ratio):
        self.xk = xk
        self.param_name = param_name
        n_best = int(len(x_obs_prior) * best_ratio)
        
        y_sorted_index = np.argsort(y_obs_prior)
        y_sorted = y_obs_prior[y_sorted_index]
#         x_sorted = [x_obs_prior[i][param_name] for i in y_sorted_index]
        x_sorted = x_obs_prior[y_sorted_index]


        x_best = x_sorted[:n_best]
        y_best = y_sorted[:n_best]

        x_worst = x_sorted[n_best:]
        y_worst = y_sorted[n_best:]
        
        max_xk = max(xk)
        self.best_prior_counts = np.bincount(x_best, minlength=max_xk+1)
        self.best_prior_counts[xk] += self.prior_weights
        self.best_yk = self.best_prior_counts / sum(self.best_prior_counts)
        
#         self.best_prob = stats.rv_discrete(values=(xk, self.best_yk))

        self.worst_prior_counts = np.bincount(x_worst, minlength=max_xk+1)
        self.worst_prior_counts[xk] += self.prior_weights
        self.worst_yk = self.worst_prior_counts / sum(self.worst_prior_counts)
#         display('probabilities {} {}'.format(self.best_yk, self.worst_yk))
#         self.worst_prob = stats.rv_discrete(values=(xk, self.worst_yk))
        
        
    def update_probability(self, param_name, xk, x_obs, y_obs,best_ratio): 
        n_best = int(len(x_obs) * best_ratio)
        #print('Updating probability using ', len(x_obs), ' prior? ' , self.use_prior)
        
        y_sorted_index = np.argsort(y_obs)
        y_sorted = y_obs[y_sorted_index]
        x_sorted = x_obs[y_sorted_index]
    
        x_best = x_sorted[:n_best]
        y_best = y_sorted[:n_best]

        x_worst = x_sorted[n_best:]
        y_worst = y_sorted[n_best:]
         
        max_xk = max(xk)
        counts = np.bincount(x_best, minlength=max_xk+1)
        if self.use_prior:
            counts = counts + _default_prior_prob_weight*(self.best_prior_counts / sum(self.best_prior_counts))
        else:
            counts[xk] += self.prior_weights
            
        self.best_yk = counts / sum(counts)
#         self.best_prob = stats.rv_discrete(values=(xk, self.best_yk))

        counts = np.bincount(x_worst, minlength=max_xk+1)
        if self.use_prior:
            counts = counts + _default_prior_prob_weight*(self.worst_prior_counts / sum(self.worst_prior_counts)) 
        else:
            counts[xk] += self.prior_weights
            
        self.worst_yk = counts / sum(counts)
#         self.worst_prob = stats.rv_discrete(values=(xk, self.worst_yk))
        
#     def get_candidates(self, csize):
#         candidates = self.best_prob.rvs(size=csize)
#         return candidates
    
    def get_lx(self, x):
        return self.best_yk[x]
    
    def get_gx(self, x):
        return self.worst_yk[x]
    
    def get_param_name(self):
        return self.param_name

