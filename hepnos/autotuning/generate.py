import sys
import os
import argparse
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from deephyper.problem import HpProblem


def __add_parameter_to_parser(parser, name, default, domain, description):
    parser.add_argument('--'+name, default=default, required=False,
                        help=description)

def __add_parameter_to_problem(problem, name, default, domain, description):
    problem.add_hyperparameter(domain, name, default_value=default)


def __fill_context(context, add_parameter):
    add_parameter(context, "busy_spin", False, [True, False],
        "Whether Mercury should busy-spin instead of block")
    add_parameter(context, "hepnos_progress_thread", False, [True, False],
        "Whether to use a dedicated progress thread in HEPnOS")
    add_parameter(context, "hepnos_num_threads", 0, (0, 63),
        "Number of threads used for serving RPC requests")
    add_parameter(context, "hepnos_num_event_databases", 1, (1, 16),
        "Number of databases per process used to store events")
    add_parameter(context, "hepnos_num_product_databases", 1, (1, 16),
        "Number of databases per process used to store products")
    add_parameter(context, "hepnos_num_providers", 1, (1, 32),
        "Number of database providers per process")
    add_parameter(context, "hepnos_pool_type", 'fifo_wait', ['fifo','fifo_wait','prio_wait'],
        "Thread-scheduling policity used by Argobots pools")
    add_parameter(context, "hepnos_pes_per_node", 2, [1, 2, 4, 8, 16, 32],
        "Number of HEPnOS processes per node")
    add_parameter(context, "loader_progress_thread", True, [True, False],
        "Whether to use a dedicated progress thread in the Dataloader")
    add_parameter(context, "loader_batch_size", 512, (1, 2048, "log-uniform"),
        "Size of the batches of events sent by the Dataloader to HEPnOS")
    add_parameter(context, "loader_pes_per_node", 2, [1, 2, 4, 8, 16],
        "Number of processes per node for the Dataloader")
    add_parameter(context, "loader_async", False, [True, False],
        "Whether to use the HEPnOS AsyncEngine in the Dataloader")
    add_parameter(context, "loader_async_threads", 1, (1, 63, "log-uniform"),
        "Number of threads for the AsyncEngine to use")
    add_parameter(context, "pep_progress_thread", False, [True, False],
        "Whether to use a dedicated progress thread in the PEP step")
    add_parameter(context, "pep_num_threads", 4, (1, 31),
        "Number of threads used for processing in the PEP step")
    add_parameter(context, "pep_ibatch_size", 128, (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are loading events from HEPnOS")
    add_parameter(context, "pep_obatch_size", 128, (8, 1024, "log-uniform"),
        "Batch size used when PEP processes are exchanging events among themselves")
    add_parameter(context, "pep_pes_per_node", 8, [1, 2, 4, 8, 16, 32],
        "Number of processes per node for the PEP step")
    add_parameter(context, "pep_use_preloading", True, [True, False],
        "Whether the PEP step should use product-preloading")


def generate_deephyper_problem():
    problem = HpProblem()
    __fill_context(problem, __add_parameter_to_problem)
    return problem

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate an experiment')
    __fill_context(parser, __add_parameter_to_parser)
    args = parser.parse_args()
    print(args)
    problem = generate_deephyper_problem()
    print(problem)
