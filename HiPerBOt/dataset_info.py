
import pandas as pd
import numpy as np
from Utilities import Utilities as utils
import matplotlib as matplotlib
import matplotlib.pyplot as plt

class DatasetInfo:

  def __init__(self, dName):
    self.dName = dName
    #dName = 'lulesh4_exec'
    # dName = 'hypre'
    # dName = 'mm'
    # dName = 'openAtom'
    # dName = 'kripke_exec'
    # dName = 'kripke'
    # dName = 'kripke_raja'
    self.nIter = 8 # Number of iterations for adaptive sampling (to_add samples in each iter)
    self.perc_optimal= 5 # Percentile of good configurations
    self.perc_bad= 90 # 90 above is worst configuration
    self.to_add = 1 #50 #0 # Uncomment for sensitivity # In each iteration number of samples added. Add 50 in each iteration
    self.train_size = 10 #50 # default is 50 [10,20,50,70,100]
    self.gamma_perc = 0.2 #[0.02,0.05,0.1,0.2,0.5]
    if dName == 'hypre':
        self.test_size = 0.991 #0.98 # 1-0.98 are used as the initial samples. Start with 100 initial samples.
        self.nIter = 9
    elif dName == 'kripke_exec':
        self.test_size = 0.98 # default 0.95
        self.to_add = 16
        self.nIter = 11
    elif dName == 'openAtom':
        self.test_size = 0.99563172043#0.99
        self.nIter = 9
    elif dName == 'kripke':
        self.test_size = 0.9978 # default 0.995
        self.nIter = 9
    elif dName == 'lulesh4_exec':
        self.test_size = 0.9903# default 0.98
        self.nIter = 9
    
    elif dName == 'lulesh3_exec':
        self.test_size = 0.996
    elif dName == 'kripke_raja':
        self.test_size = 0.99777#0.995
        self.nIter = 9
    elif dName == 'mm':
        self.test_size = 0.98
        self.nIter = 9
    elif dName == 'DH_surrogate':
        self.test_size = 0.98
        self.nIter = 101
    #self.nIter = 1 # Uncomment for sensitivity

  def initialize_dataset(self):
    util = utils()
    feats_drop = []
    # Tizona is used to create https://github.com/emcastillo/Tizona
    # launch scripts
    if self.dName == 'hypre':
        filename = "datasets/powerperf/binarized/hypre_27pt.64nodes.2000.norm.binary.csv"
        response = "ExecTime" # Dependent variable
        self.X_bin, self.y_bin = util.load_data(filename, response)
        pkg100_indices = np.where(self.X_bin['PKG_LIMIT']==100)[0]
        self.X_bin, self.y_bin = self.X_bin.iloc[pkg100_indices], self.y_bin[pkg100_indices]
        self.X_bin = self.X_bin[['Ranks','OMP','Solver_s0','Solver_s2','Solver_s3','Solver_s51','Solver_s61','Solver_s9','Smoother_3', \
               'Smoother_4','Smoother_6','Smoother_8','Smoother_13','Smoother_14','Smoother_16','PMX','MU']]
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, response_name=response, response_norm=False)

    elif self.dName == 'DH_surrogate':
        filename = "/gpfs/fs0/project/FastBayes/Sandeep/github_repos/HEPnOS-Autotuning/HiPerBOt/datasets/DH_expt/10k-samples.csv"
        response = "objective" # Dependent variable
        self.X_bin_all, self.y_bin_all = util.load_data(filename, response)

        self.X_bin_all = self.X_bin_all[['busy_spin','hepnos_num_event_databases','hepnos_num_product_databases','hepnos_num_providers',
        'hepnos_num_rpc_threads','hepnos_pes_per_node','hepnos_pool_type','hepnos_progress_thread','loader_async',
        'loader_async_threads','loader_batch_size','loader_pes_per_node','loader_progress_thread','pep_ibatch_size',
        'pep_no_preloading','pep_no_rdma','pep_num_threads','pep_obatch_size','pep_pes_per_node','pep_progress_thread']]


        self.X_bin = self.X_bin_all.iloc[50:]
        self.X_bin_init1 = self.X_bin_all.iloc[0:10]
        self.X_bin_init2 = self.X_bin_all.iloc[10:20]
        self.X_bin_init3 = self.X_bin_all.iloc[20:30]
        self.X_bin_init4 = self.X_bin_all.iloc[30:40]
        self.X_bin_init5 = self.X_bin_all.iloc[40:50]

        self.y_bin = self.y_bin_all[50:]
        self.y_bin_init1 = self.y_bin_all[0:10]
        self.y_bin_init2 = self.y_bin_all[10:20]
        self.y_bin_init3 = self.y_bin_all[20:30]
        self.y_bin_init4 = self.y_bin_all[30:40]
        self.y_bin_init5 = self.y_bin_all[40:50]


        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, response_name=response, response_norm=False)
    elif self.dName == 'kripke':
        filename = "datasets/powerperf/binarized/kripke.16nodes.2000_input.l0.norm.binary.csv"
        response = "Energy"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        feats_drop = ['Input_2000', 'ScatteringOrder_l0', 'Nodes_16', \
                  'Input_12000', 'ScatteringOrder_l9', 'Nodes_64', 'Layout_0', \
                  'DRAM_LIMIT', 'DRAMPowerPerNode', 'ProcessorPower', 'Method_sweep',\
                 'ProcessorPowerPerNode', 'DRAMPower', 'AvgTemp', 'AvgFreq',\
                  'AvgArithFpu','AvgInst','AvgIpc', 'ExecTime']
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, feats_drop=feats_drop, response_name=response, response_norm=False)
    elif self.dName == 'kripke_exec':
        filename = "datasets/powerperf/binarized/kripke.16nodes.12000_input.l0.norm.binary.csv"
        response = "ExecTime"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        pkg100_indices = np.where(self.X_bin['PKG_LIMIT']==100)[0]
        self.X_bin, self.y_bin = self.X_bin.iloc[pkg100_indices], self.y_bin[pkg100_indices]
        feats_drop = ['Input_2000', 'ScatteringOrder_l0', 'Nodes_16', \
                  'Input_12000', 'ScatteringOrder_l9', 'Nodes_64', 'Layout_0', \
                  'DRAM_LIMIT', 'DRAMPowerPerNode', 'ProcessorPower', 'Method_sweep',\
                 'ProcessorPowerPerNode', 'DRAMPower', 'AvgTemp', 'AvgFreq',\
                  'AvgArithFpu','AvgInst','AvgIpc', 'PKG_LIMIT']
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, feats_drop=feats_drop, response_name=response, response_norm=False)
    elif self.dName == 'openAtom':
        filename = "datasets/powerperf/binarized/openAtom.water.128nodes.binary.csv"
        response = "ExecTime"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, response_name=response, response_norm=False)
    elif self.dName == 'lulesh4_exec':
        filename = "datasets/powerperf/binarized/lulesh.set4.binary.csv"
        response = "ExecTime"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        pkgS1_indices = np.where(self.X_bin['stores_always']==1.0)[0]
        self.X_bin, self.y_bin = self.X_bin.iloc[pkgS1_indices], self.y_bin[pkgS1_indices]
        feats_drop = ['stores_always', 'stores_auto', 'stores_never']
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, feats_drop=feats_drop, response_name='ExecTime', response_norm=False)
    elif self.dName == 'lulesh3_exec':
        filename = "datasets/powerperf/binarized/lulesh.set3.binary.csv"
        response = "ExecTime"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, response_name='ExecTime', response_norm=False)
    elif self.dName == 'kripke_raja':
        filename = "datasets/powerperf/binarized/kripke.raja_policies.numeric_parameters.average.csv"
        response = "percent_of_fastest"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        self.y_bin = 101 - self.y_bin
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, response_name=response, response_norm=False)
    elif self.dName == 'mm':
        filename = "datasets/powerperf/binarized/mm.set1.binary.csv"
        response = "ExecTime"
        self.X_bin, self.y_bin = util.load_data(filename, response)
        feats_drop = ['omp']
        data_bin_pd = util.data_norm(self.X_bin, self.y_bin, response_name='ExecTime', response_norm=False)
    
    
    matplotlib.rcParams.update({'font.size': 24})
    plt.figure(figsize=(12,8))
    # plt.grid(True)
    ax1 = plt.gca()
    plt.xlabel('Execution time (s)', fontsize=24); #plt.ylabel('f(x)')
    plt.xscale('log')
    ax1.set_ylabel('# configurations', fontsize=24)
    plt.hist(self.y_bin, 300)
    plt.axis('tight')
    plt.tick_params(labelsize=20)
    plt.savefig('plots/' + self.dName + '_dist.pdf',bbox_inches='tight')
    #plt.show()
    
    # plt.xscale('log')
    # plt.hist(self.y_bin,50)
    # plt.show() # Histogram below shows on x axis the exec time and y axis the number of configurations in that bucket.
    
    n_feat_bin = data_bin_pd.shape[1]-1 # Histogram of the dependent variable
    
    #print(self.X_bin.columns)
    
    self.X_new_bin = self.X_bin.copy()
    if feats_drop is not None:
        self.X_new_bin = self.X_new_bin.drop(feats_drop, axis=1)
    self.X_new_bin[response] = self.y_bin
    
    self.y_new_bin = self.X_new_bin[response].values
    #print(type(self.y_new_bin))
    self.X_new_bin = self.X_new_bin.iloc[:,:n_feat_bin]
    #print(len(self.X_new_bin))
    
    for label_idx, datalabel in enumerate(self.X_new_bin.columns):
        xk = np.unique(self.X_new_bin[datalabel].values)
        #print(datalabel, xk)
    
    self.X_bin_u = self.X_new_bin.copy()

    if self.dName == 'lulesh4_exec':
    
        self.X_bin_u['strategy']=0
        feats_drop = ['strategy_block', 'strategy_loop', 'strategy_routine', 'strategy_trace']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['strategy_block']==1]
        self.X_bin_u.loc[sbl,'strategy']=0
        sbl= self.X_new_bin.index[self.X_new_bin['strategy_loop']==1]
        self.X_bin_u.loc[sbl,'strategy']=1
        sbl= self.X_new_bin.index[self.X_new_bin['strategy_routine']==1]
        self.X_bin_u.loc[sbl,'strategy']=2
        sbl= self.X_new_bin.index[self.X_new_bin['strategy_trace']==1]
        self.X_bin_u.loc[sbl,'strategy']=3
    elif self.dName == 'hypre':
        self.X_bin_u['Solver'] = 0
        feats_drop = ['Solver_s0', 'Solver_s2', 'Solver_s3', 'Solver_s9', 'Solver_s51', 'Solver_s61']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s0']==1]
        self.X_bin_u.loc[sbl,'Solver']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s2']==1]
        self.X_bin_u.loc[sbl,'Solver']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s3']==1]
        self.X_bin_u.loc[sbl,'Solver']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s9']==1]
        self.X_bin_u.loc[sbl,'Solver']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s51']==1]
        self.X_bin_u.loc[sbl,'Solver']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s61']==1]
        self.X_bin_u.loc[sbl,'Solver']=5
    
        self.X_bin_u['Smoother']=0
        feats_drop = ['Smoother_3', 'Smoother_4', 'Smoother_6', 'Smoother_8', 'Smoother_13', 'Smoother_14', 'Smoother_16']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_3']==1]
        self.X_bin_u.loc[sbl,'Smoother']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_4']==1]
        self.X_bin_u.loc[sbl,'Smoother']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_6']==1]
        self.X_bin_u.loc[sbl,'Smoother']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_8']==1]
        self.X_bin_u.loc[sbl,'Smoother']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_13']==1]
        self.X_bin_u.loc[sbl,'Smoother']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_14']==1]
        self.X_bin_u.loc[sbl,'Smoother']=5
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_16']==1]
        self.X_bin_u.loc[sbl,'Smoother']=6
    
    elif self.dName == 'HYPRE':
        self.X_bin_u['Solver']=0
        feats_drop = ['Solver_s0', 'Solver_s2', 'Solver_s3', 'Solver_s9', 'Solver_s51', 'Solver_s61']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s0']==1]
        self.X_bin_u.loc[sbl,'Solver']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s2']==1]
        self.X_bin_u.loc[sbl,'Solver']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s3']==1]
        self.X_bin_u.loc[sbl,'Solver']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s9']==1]
        self.X_bin_u.loc[sbl,'Solver']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s51']==1]
        self.X_bin_u.loc[sbl,'Solver']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s61']==1]
        self.X_bin_u.loc[sbl,'Solver']=5
    
        self.X_bin_u['Smoother']=0
        feats_drop = ['Smoother_3', 'Smoother_4', 'Smoother_6', 'Smoother_8', 'Smoother_13', 'Smoother_14', 'Smoother_16']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_3']==1]
        self.X_bin_u.loc[sbl,'Smoother']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_4']==1]
        self.X_bin_u.loc[sbl,'Smoother']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_6']==1]
        self.X_bin_u.loc[sbl,'Smoother']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_8']==1]
        self.X_bin_u.loc[sbl,'Smoother']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_13']==1]
        self.X_bin_u.loc[sbl,'Smoother']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_14']==1]
        self.X_bin_u.loc[sbl,'Smoother']=5
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_16']==1]
        self.X_bin_u.loc[sbl,'Smoother']=6
    
        feats_drop_other = ['Nodes_64', 'Nodes_16', 'Input_2000', 'DRAM_LIMIT', 'Coarsening_pmis']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop_other, axis=1)
    
        self.X_bin_u['Ranks'] = self.X_bin_u['Ranks']/64
        # print self.X_bin_u
    
    elif self.dName == 'kripke_exec':
        self.X_bin_u['Nesting']=0
        feats_drop = ['Nesting_DGZ', 'Nesting_DZG', 'Nesting_GDZ', 'Nesting_GZD', 'Nesting_ZDG', 'Nesting_ZGD']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_DGZ']==1]
        self.X_bin_u.loc[sbl,'Nesting']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_DZG']==1]
        self.X_bin_u.loc[sbl,'Nesting']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_GDZ']==1]
        self.X_bin_u.loc[sbl,'Nesting']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_GZD']==1]
        self.X_bin_u.loc[sbl,'Nesting']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_ZDG']==1]
        self.X_bin_u.loc[sbl,'Nesting']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_ZGD']==1]
        self.X_bin_u.loc[sbl,'Nesting']=5
    
        self.X_bin_u['Ranks'] = self.X_bin_u['Ranks']/64
        # print self.X_bin_u
    elif self.dName == 'kripke':
        self.X_bin_u['Nesting']=0
        feats_drop = ['Nesting_DGZ', 'Nesting_DZG', 'Nesting_GDZ', 'Nesting_GZD', 'Nesting_ZDG', 'Nesting_ZGD']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_DGZ']==1]
        self.X_bin_u.loc[sbl,'Nesting']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_DZG']==1]
        self.X_bin_u.loc[sbl,'Nesting']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_GDZ']==1]
        self.X_bin_u.loc[sbl,'Nesting']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_GZD']==1]
        self.X_bin_u.loc[sbl,'Nesting']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_ZDG']==1]
        self.X_bin_u.loc[sbl,'Nesting']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_ZGD']==1]
        self.X_bin_u.loc[sbl,'Nesting']=5
    
        self.X_bin_u['Ranks'] = self.X_bin_u['Ranks']/64
        # print self.X_bin_u

  def initialize_dataset_tl(self):
    util = utils()
    
    # Tizona is used to create https://github.com/emcastillo/Tizona
    # launch scripts
    if self.dName == 'KRIPKE.L0':
        filename = "datasets/tl/kripke.64nodes.2000_input.l0.norm.binary.csv"
        response = "ExecTime"
        feats_drop = ['DRAMPowerPerNode', 'ProcessorPowerPerNode', 'ProcessorPower', 'DRAMPower', 'AvgTemp', 'AvgFreq', 'AvgArithFpu', 'AvgInst', 'AvgIpc']
    #     feats_drop = ['DRAMPowerPerNode', 'ProcessorPowerPerNode', 'ProcessorPower', 'DRAMPower', 'AvgTemp', 'AvgFreq', 'AvgArithFpu', 'AvgInst', 'AvgIpc', 'AvgUnhaltedThread']
        X_bin_temp, y_bin_temp = util.load_data(filename, response)
    #     data_bin_pd = util.data_norm(X_bin, y_bin, response_name='ExecTime', response_norm=False)
        self.X_new_bin = X_bin_temp.copy()
        if feats_drop is not None:
            self.X_new_bin = self.X_new_bin.drop(feats_drop, axis=1)
    
        filename = "datasets/tl/kripke.16nodes.2000_input.l0.norm.binary.csv"
        X_small_bin_temp, y_small_bin_temp = util.load_data(filename, response)
    #     data_bin_pd = util.data_norm(X_bin, y_bin, response_name='ExecTime', response_norm=False)
        self.X_new_small_bin = X_small_bin_temp.copy()
        if feats_drop is not None:
            self.X_new_small_bin = self.X_new_small_bin.drop(feats_drop, axis=1)
    elif self.dName == 'HYPRE':
        filename = "datasets/tl/hypre_27pt.64nodes.2000.norm.binary.csv"
        response = "ExecTime"
        feats_drop = ['DRAMPowerPerNode', 'ProcessorPowerPerNode', 'ProcessorPower', 'DRAMPower']
    #     feats_drop = ['DRAMPowerPerNode', 'ProcessorPowerPerNode', 'ProcessorPower', 'DRAMPower', 'AvgTemp', 'AvgFreq', 'AvgArithFpu', 'AvgInst', 'AvgIpc', 'AvgUnhaltedThread']
        X_bin_temp, y_bin_temp = util.load_data(filename, response)
    #     data_bin_pd = util.data_norm(X_bin, y_bin, response_name='ExecTime', response_norm=False)
        self.X_new_bin = X_bin_temp.copy()
        if feats_drop is not None:
            self.X_new_bin = self.X_new_bin.drop(feats_drop, axis=1)
    
        filename = "datasets/tl/hypre_27pt.16nodes.2000.norm.binary.csv"
        X_small_bin_temp, y_small_bin_temp = util.load_data(filename, response)
    #     data_bin_pd = util.data_norm(X_bin, y_bin, response_name='ExecTime', response_norm=False)
        self.X_new_small_bin = X_small_bin_temp.copy()
        if feats_drop is not None:
            self.X_new_small_bin = self.X_new_small_bin.drop(feats_drop, axis=1)
        
        
    self.y_new_bin = y_bin_temp.flatten()
    self.y_new_small_bin = y_small_bin_temp.flatten()
    # y_bin_temp = y_bin_temp.flatten()
    # y_new_bin = y_bin_temp
    # y_small_bin_temp = y_small_bin_temp.flatten()
    # plt.hist(y_bin,50)
    # plt.show() # Histogram below shows on x axis the exec time and y axis the number of configurations in that bucket.
        
        
    plt.hist(self.y_new_small_bin,50)
    #plt.show() # Histogram below shows on x axis the exec time and y axis the number of configurations in that bucket.
        
    # n_feat_bin = data_bin_pd.shape[1]-1 # Histogram of the dependent variable
    
    # print data_bin_pd.columns
    
    
    # # X_new_bin = data_bin_pd.iloc[:,:n_feat_bin]
    # # y_new_bin = data_bin_pd.iloc[:,n_feat_bin]
    # X_new_bin = X_bin.copy()
    # if feats_drop is not None:
    #     X_new_bin = X_new_bin.drop(feats_drop, axis=1)
    # X_new_bin[response] = y_bin
    
    # y_new_bin = X_new_bin[response].values
    # print type(y_new_bin)
    # X_new_bin = X_new_bin.iloc[:,:n_feat_bin]
    # print len(X_new_bin)
    # print len(X_new_bin)
    # print X_new_bin.iloc[10,:12]
    # print X_new_bin.iloc[1,:12]
    # print data_bin_pd.iloc[10,:12]
    # print data_bin_pd.iloc[1,:12]
    # print y_new_bin
    # perf_label = data_bin_pd[response].copy()
    # print data_bin_pd.iloc[:,:n_feat_bin]
    
    for datalabel in self.X_new_bin.columns:
        xk = np.unique(self.X_new_bin[datalabel]).tolist()
        print(datalabel, xk)
    
    for datalabel in self.X_new_small_bin.columns:
        xk = np.unique(self.X_new_small_bin[datalabel]).tolist()
        print(datalabel, xk)
        
    self.X_bin_u = self.X_new_bin.copy()
    
    if self.dName == 'HYPRE':
        self.X_bin_u['Solver']=0
        feats_drop = ['Solver_s0', 'Solver_s2', 'Solver_s3', 'Solver_s9', 'Solver_s51', 'Solver_s61']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s0']==1]
        self.X_bin_u.loc[sbl,'Solver']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s2']==1]
        self.X_bin_u.loc[sbl,'Solver']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s3']==1]
        self.X_bin_u.loc[sbl,'Solver']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s9']==1]
        self.X_bin_u.loc[sbl,'Solver']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s51']==1]
        self.X_bin_u.loc[sbl,'Solver']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Solver_s61']==1]
        self.X_bin_u.loc[sbl,'Solver']=5
    
        self.X_bin_u['Smoother']=0
        feats_drop = ['Smoother_3', 'Smoother_4', 'Smoother_6', 'Smoother_8', 'Smoother_13', 'Smoother_14', 'Smoother_16']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_3']==1]
        self.X_bin_u.loc[sbl,'Smoother']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_4']==1]
        self.X_bin_u.loc[sbl,'Smoother']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_6']==1]
        self.X_bin_u.loc[sbl,'Smoother']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_8']==1]
        self.X_bin_u.loc[sbl,'Smoother']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_13']==1]
        self.X_bin_u.loc[sbl,'Smoother']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_14']==1]
        self.X_bin_u.loc[sbl,'Smoother']=5
        sbl= self.X_new_bin.index[self.X_new_bin['Smoother_16']==1]
        self.X_bin_u.loc[sbl,'Smoother']=6
    
        feats_drop_other = ['Nodes_64', 'Nodes_16', 'Input_2000', 'DRAM_LIMIT', 'Coarsening_pmis']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop_other, axis=1)
    
        self.X_bin_u['Ranks'] = self.X_bin_u['Ranks']/64
        # print self.X_bin_u
    
        self.X_small_bin_u = self.X_new_small_bin.copy()
        self.X_small_bin_u['Solver']=0
        feats_drop = ['Solver_s0', 'Solver_s2', 'Solver_s3', 'Solver_s9', 'Solver_s51', 'Solver_s61']
        if feats_drop is not None:
            self.X_small_bin_u = self.X_small_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Solver_s0']==1]
        self.X_small_bin_u.loc[sbl,'Solver']=0
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Solver_s2']==1]
        self.X_small_bin_u.loc[sbl,'Solver']=1
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Solver_s3']==1]
        self.X_small_bin_u.loc[sbl,'Solver']=2
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Solver_s9']==1]
        self.X_small_bin_u.loc[sbl,'Solver']=3
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Solver_s51']==1]
        self.X_small_bin_u.loc[sbl,'Solver']=4
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Solver_s61']==1]
        self.X_small_bin_u.loc[sbl,'Solver']=5
    
        self.X_small_bin_u['Smoother']=0
        feats_drop = ['Smoother_3', 'Smoother_4', 'Smoother_6', 'Smoother_8', 'Smoother_13', 'Smoother_14', 'Smoother_16']
        if feats_drop is not None:
            self.X_small_bin_u = self.X_small_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_3']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=0
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_4']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=1
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_6']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=2
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_8']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=3
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_13']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=4
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_14']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=5
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Smoother_16']==1]
        self.X_small_bin_u.loc[sbl,'Smoother']=6
    
        feats_drop_other = ['Nodes_64', 'Nodes_16', 'Input_2000', 'DRAM_LIMIT', 'Coarsening_pmis']
        if feats_drop is not None:
            self.X_small_bin_u = self.X_small_bin_u.drop(feats_drop_other, axis=1)
    
        self.X_small_bin_u['Ranks'] = self.X_small_bin_u['Ranks']/16
    elif self.dName == 'KRIPKE.L0':
        self.X_bin_u['Nesting']=0
        feats_drop = ['Nesting_DGZ', 'Nesting_DZG', 'Nesting_GDZ', 'Nesting_GZD', 'Nesting_ZDG', 'Nesting_ZGD']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_DGZ']==1]
        self.X_bin_u.loc[sbl,'Nesting']=0
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_DZG']==1]
        self.X_bin_u.loc[sbl,'Nesting']=1
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_GDZ']==1]
        self.X_bin_u.loc[sbl,'Nesting']=2
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_GZD']==1]
        self.X_bin_u.loc[sbl,'Nesting']=3
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_ZDG']==1]
        self.X_bin_u.loc[sbl,'Nesting']=4
        sbl= self.X_new_bin.index[self.X_new_bin['Nesting_ZGD']==1]
        self.X_bin_u.loc[sbl,'Nesting']=5
    
        feats_drop_other = ['Nodes_64', 'Nodes_16', 'Input_12000', 'Input_2000', 'ScatteringOrder_l0','ScatteringOrder_l9', 'Layout_0', 'Method_sweep', 'DRAM_LIMIT']
        if feats_drop is not None:
            self.X_bin_u = self.X_bin_u.drop(feats_drop_other, axis=1)
    
        self.X_bin_u['Ranks'] = self.X_bin_u['Ranks']/64
        # print self.X_bin_u
    
        self.X_small_bin_u = self.X_new_small_bin.copy()
        self.X_small_bin_u['Nesting']=0
        feats_drop = ['Nesting_DGZ', 'Nesting_DZG', 'Nesting_GDZ', 'Nesting_GZD', 'Nesting_ZDG', 'Nesting_ZGD']
        if feats_drop is not None:
            self.X_small_bin_u = self.X_small_bin_u.drop(feats_drop, axis=1)
    
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Nesting_DGZ']==1]
        self.X_small_bin_u.loc[sbl,'Nesting']=0
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Nesting_DZG']==1]
        self.X_small_bin_u.loc[sbl,'Nesting']=1
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Nesting_GDZ']==1]
        self.X_small_bin_u.loc[sbl,'Nesting']=2
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Nesting_GZD']==1]
        self.X_small_bin_u.loc[sbl,'Nesting']=3
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Nesting_ZDG']==1]
        self.X_small_bin_u.loc[sbl,'Nesting']=4
        sbl= self.X_new_small_bin.index[self.X_new_small_bin['Nesting_ZGD']==1]
        self.X_small_bin_u.loc[sbl,'Nesting']=5
    
        feats_drop_other = ['Nodes_64', 'Nodes_16', 'Input_12000', 'Input_2000', 'ScatteringOrder_l0', 'ScatteringOrder_l9', 'Layout_0', 'Method_sweep', 'DRAM_LIMIT']
        if feats_drop is not None:
            self.X_small_bin_u = self.X_small_bin_u.drop(feats_drop_other, axis=1)
    
        self.X_small_bin_u['Ranks'] = self.X_small_bin_u['Ranks']/16
    
        
    dataset_len = len(self.X_bin_u)
    print('dataset_len ', dataset_len)
    print('Small: ', len(self.y_new_small_bin), ' Target: ', len(self.y_new_bin))  
    print(int(0.01*len(self.y_new_bin))+100)
