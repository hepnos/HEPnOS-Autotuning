import os
from deephyper.problem import HpProblem

Problem = HpProblem(seed=2021)

# the following is the old definition of the Problem
"""
# 1. step
Problem.add_hyperparameter((0, 31), "hepnos_num_threads")
Problem.add_hyperparameter((1, 10), "hepnos_num_databases")
Problem.add_hyperparameter([True, False], "busy_spin")
Problem.add_hyperparameter([True, False], "loader_progress_thread")
Problem.add_hyperparameter((1, 2048, "log-uniform"), "loader_batch_size")

# when "enable_step == True"
# 2. step:
enable_pep = bool(int(os.environ.get("DH_HEPNOS_ENABLE_PEP", 0)))
if enable_pep:
    Problem.add_hyperparameter((1, 31), "pep_num_threads")
    Problem.add_hyperparameter((8, 1024, "log-uniform"), "pep_ibatch_size")
    Problem.add_hyperparameter((8, 1024, "log-uniform"), "pep_obatch_size")
    Problem.add_hyperparameter([True, False], "pep_use_preloading")

# 3. step:
# Problem.add_hyperparameter((1, 64), "pep_pes_per_node")
# Problem.add_hyperparameter((1, 64), "pep_cores_per_pe")
"""

def add_parameter(problem, name, domain, description=""):
    problem.add_hyperparameter(domain, name)

step = int(os.environ.get("DH_HEPNOS_EXP_STEP", 1))

# Step 1: Data-loader only, at small scale

add_parameter(Problem, "busy_spin", [True, False],
    "Whether Mercury should busy-spin instead of block")
add_parameter(Problem, "hepnos_progress_thread", [True, False],
    "Whether to use a dedicated progress thread in HEPnOS")
add_parameter(Problem, "hepnos_num_threads", (0, 63),
    "Number of threads used for serving RPC requests")
add_parameter(Problem, "hepnos_num_event_databases", (1, 16),
    "Number of databases per process used to store events")
add_parameter(Problem, "hepnos_num_product_databases", (1, 16),
    "Number of databases per process used to store products")
add_parameter(Problem, "hepnos_num_providers", (1, 32),
    "Number of database providers per process")
add_parameter(Problem, "hepnos_pool_type", ['fifo','fifo_wait','prio_wait'],
    "Thread-scheduling policity used by Argobots pools")
add_parameter(Problem, "hepnos_pes_per_node", [1, 2, 4, 8, 16, 32],
    "Number of HEPnOS processes per node")

add_parameter(Problem, "loader_progress_thread", [True, False],
    "Whether to use a dedicated progress thread in the Dataloader")
add_parameter(Problem, "loader_batch_size", (1, 2048, "log-uniform"),
    "Size of the batches of events sent by the Dataloader to HEPnOS")
add_parameter(Problem, "loader_pes_per_node", [1, 2, 4, 8, 16, 32],
    "Number of processes per node for the Dataloader")

# Step 2: We add the PEP step, still at small scall
if step >= 2:
    add_parameter(Problem, "pep_progress_thread", [True, False],
        "Whether to use a dedicated progress thread in the PEP step")
    add_parameter(Problem, "pep_num_threads", (1, 31),
        "Number of threads used for processing in the PEP step")
    add_parameter(Problem, "pep_ibatch_size", (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are loading events from HEPnOS")
    add_parameter(Problem, "pep_obatch_size", (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are exchanging events among themselves")
    add_parameter(Problem, "pep_pes_per_node", [1, 2, 4, 8, 16, 32],
        "Number of processes per node for the PEP step")

# Step 3: We add some new parameters
if step >= 3:
    add_parameter(Problem, "loader_async", [True, False],
        "Whether to use the HEPnOS AsyncEngine in the Dataloader")
    add_parameter(Problem, "loader_async_threads", (1, 63, "log-uniform"),
        "Number of threads for the AsyncEngine to use")
    add_parameter(Problem, "pep_use_preloading", [True, False],
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
