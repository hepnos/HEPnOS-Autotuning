import logging
import os
import pickle
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

#!!! DeepHyper Problem [START]
from deephyper.evaluator import profile, Evaluator
from deephyper.evaluator.callback import LoggerCallback
from deephyper.search.hps import AMBS

def __add_parameter_to_problem(problem, name, type, default, domain, description):
    """Callback to add a parameter to a DeepHyper problem."""
    problem.add_hyperparameter(domain, name, default_value=default)


def __fill_context(context, add_parameter, disable_pep=False, more_params=True):
    """Fill either an argparse parser or a DeepHyper problem using
    the provided add_parameter callback."""

    add_parameter(context, "busy_spin", bool, False, [True, False],
        "Whether Mercury should busy-spin instead of block")
    add_parameter(context, "hepnos_progress_thread", bool, False, [True, False],
        "Whether to use a dedicated progress thread in HEPnOS")
    add_parameter(context, "hepnos_num_rpc_threads", int, 0, (0, 63),
        "Number of threads used for serving RPC requests")
    add_parameter(context, "hepnos_num_event_databases", int, 1, (1, 16),
        "Number of databases per process used to store events")
    add_parameter(context, "hepnos_num_product_databases", int, 1, (1, 16),
        "Number of databases per process used to store products")
    add_parameter(context, "hepnos_num_providers", int, 1, (1, 32),
        "Number of database providers per process")
    add_parameter(context, "hepnos_pool_type", str, 'fifo_wait', ['fifo','fifo_wait'],
        "Thread-scheduling policity used by Argobots pools")
    add_parameter(context, "hepnos_pes_per_node", int, 2, [1, 2, 4, 8, 16, 32],
        "Number of HEPnOS processes per node")
    add_parameter(context, "loader_progress_thread", bool, False, [True, False],
        "Whether to use a dedicated progress thread in the Dataloader")
    add_parameter(context, "loader_batch_size", int, 512, (1, 2048, "log-uniform"),
        "Size of the batches of events sent by the Dataloader to HEPnOS")
    add_parameter(context, "loader_pes_per_node", int, 2, [1, 2, 4, 8, 16],
        "Number of processes per node for the Dataloader")
    if more_params:
        add_parameter(context, "loader_async", bool, False, [True, False],
            "Whether to use the HEPnOS AsyncEngine in the Dataloader")
        add_parameter(context, "loader_async_threads", int, 1, (1, 63, "log-uniform"),
            "Number of threads for the AsyncEngine to use")
    if disable_pep:
        return
    add_parameter(context, "pep_progress_thread", bool, False, [True, False],
        "Whether to use a dedicated progress thread in the PEP step")
    add_parameter(context, "pep_num_threads", int, 4, (1, 31),
        "Number of threads used for processing in the PEP step")
    add_parameter(context, "pep_ibatch_size", int, 128, (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are loading events from HEPnOS")
    add_parameter(context, "pep_obatch_size", int, 128, (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are exchanging events among themselves")
    add_parameter(context, "pep_pes_per_node", int, 8, [1, 2, 4, 8, 16, 32],
        "Number of processes per node for the PEP step")
    if more_params:
        add_parameter(context, "pep_no_preloading", bool, False, [True, False],
            "Whether to disable product-preloading in PEP")
        add_parameter(context, "pep_no_rdma", bool, False, [True, False],
            "Whether to disable RDMA in PEP")

def build_deephyper_problem(disable_pep, more_params):
    """Generate a returns a DeepHyper problem."""
    from deephyper.problem import HpProblem
    problem = HpProblem()
    __fill_context(problem, __add_parameter_to_problem, disable_pep, more_params)
    return problem

@profile
def run(config):
    
    
    cols = "busy_spin,hepnos_num_event_databases,hepnos_num_product_databases,hepnos_num_providers,hepnos_num_rpc_threads,hepnos_pes_per_node,hepnos_pool_type,hepnos_progress_thread,loader_async,loader_async_threads,loader_batch_size,loader_pes_per_node,loader_progress_thread,pep_ibatch_size,pep_no_preloading,pep_no_rdma,pep_num_threads,pep_obatch_size,pep_pes_per_node,pep_progress_thread"
    cols = cols.split(",") + ["objective"]
    config["objective"] = 0

    df = pd.DataFrame(data=[config], columns=cols)

    model_path = os.path.join(HERE, "exp-DUMMY-4-false-false/surrogate.pkl")
    with open(model_path, "rb") as f:
        saved_pipeline = pickle.load(f)

    data_pipeline_model = saved_pipeline["data"]
    regr = saved_pipeline["model"]

    preprocessed_data = data_pipeline_model.transform(df)
    preds = regr.predict(preprocessed_data[:, 1:])

    preds = data_pipeline_model.transformers_[0][1].inverse_transform(preds.reshape(-1, 1))

    objective = preds[0,0]

    elapsed = np.exp(-objective)
    # time.sleep(elapsed)

    return objective

if __name__ == "__main__":
    problem = build_deephyper_problem(disable_pep=False, more_params=True)
    print(problem)

    evaluator = Evaluator.create(run, method="serial", method_kwargs={"callbacks": [LoggerCallback()]})

    search = AMBS(problem, evaluator, surrogate_model="DUMMY", random_state=42)

    results = search.search(max_evals=10_000)
    