import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from deephyper.problem import HpProblem


Problem = HpProblem()


def __add_parameter(problem, name, domain, description=""):
    problem.add_hyperparameter(domain, name)


step = int(os.environ.get("DH_HEPNOS_EXP_STEP", 1))

# Step 1: Data-loader only, at small scale

__add_parameter(Problem, "busy_spin", [True, False],
    "Whether Mercury should busy-spin instead of block")
__add_parameter(Problem, "hepnos_progress_thread", [True, False],
    "Whether to use a dedicated progress thread in HEPnOS")
__add_parameter(Problem, "hepnos_num_threads", (0, 63),
    "Number of threads used for serving RPC requests")
__add_parameter(Problem, "hepnos_num_event_databases", (1, 16),
    "Number of databases per process used to store events")
__add_parameter(Problem, "hepnos_num_product_databases", (1, 16),
    "Number of databases per process used to store products")
__add_parameter(Problem, "hepnos_num_providers", (1, 32),
    "Number of database providers per process")
__add_parameter(Problem, "hepnos_pool_type", ['fifo','fifo_wait','prio_wait'],
    "Thread-scheduling policity used by Argobots pools")
__add_parameter(Problem, "hepnos_pes_per_node", [1, 2, 4, 8, 16, 32],
    "Number of HEPnOS processes per node")

__add_parameter(Problem, "loader_progress_thread", [True, False],
    "Whether to use a dedicated progress thread in the Dataloader")
__add_parameter(Problem, "loader_batch_size", (1, 2048, "log-uniform"),
    "Size of the batches of events sent by the Dataloader to HEPnOS")
__add_parameter(Problem, "loader_pes_per_node", [1, 2, 4, 8, 16],
    "Number of processes per node for the Dataloader")

# Step 2: We add the PEP step, still at small scall
if step >= 2:
    __add_parameter(Problem, "pep_progress_thread", [True, False],
        "Whether to use a dedicated progress thread in the PEP step")
    __add_parameter(Problem, "pep_num_threads", (1, 31),
        "Number of threads used for processing in the PEP step")
    __add_parameter(Problem, "pep_ibatch_size", (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are loading events from HEPnOS")
    __add_parameter(Problem, "pep_obatch_size", (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are exchanging events among themselves")
    __add_parameter(Problem, "pep_pes_per_node", [1, 2, 4, 8, 16, 32],
        "Number of processes per node for the PEP step")

# Step 3: We add some new parameters
if step >= 3:
    __add_parameter(Problem, "loader_async", [True, False],
        "Whether to use the HEPnOS AsyncEngine in the Dataloader")
    __add_parameter(Problem, "loader_async_threads", (1, 63, "log-uniform"),
        "Number of threads for the AsyncEngine to use")
    __add_parameter(Problem, "pep_use_preloading", [True, False],
        "Whether the PEP step should use product-preloading")

# Step 4: We scale to larger experiments (no new processes)

# Note: in the above, if
#    (X_progress_thread + 1 + X_num_threads) * X_pes_per_node > 64,
# then we oversubscribe the nodes with more threads than we should.
# If this leads to performance degradation, the DeepHyper should detect
# it and avoid the corresponding regions of the parameter space.
# However it would be nice for the paper to be able to impose constraints
# like that.
#
# Note: in step 3, if loader_async is False, then the value of
# loader_async_threads is irrelevant, so it would be nice to be able
# to not sample it when loader_async is False (say that "loader_async_threads"
# is a child parameter of "loader_async".

if __name__ == "__main__":
    print(Problem)
