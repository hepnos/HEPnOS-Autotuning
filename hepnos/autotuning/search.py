import os
import argparse
import logging
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import importlib
from .platform import detect_platform


def __make_objective_function(f, exp_prefix, build_prefix, protocol, nodes_per_exp):
    if not exp_prefix.startswith('/'):
        exp_prefix = os.path.join(os.getcwd(), exp_prefix)
    def __objective(config, dequed=None):
        hepnos_nodelist = ''
        pep_nodelist = ''
        loader_nodelist = ''
        if dequed is not None:
            l = len(dequed)
            x = int(l/4.0)
            hepnos_nodelist = ','.join(dequed[:x])
            pep_nodelist = ','.join(dequed[x:])
            loader_nodelist = pep_nodelist
        return f(exp_prefix, build_prefix, protocol,
                 nodes_per_exp=nodes_per_exp,
                 hepnos_nodelist=hepnos_nodelist,
                 pep_nodelist=pep_nodelist,
                 loader_nodelist=loader_nodelist,
                 **config)
    return __objective


if __name__ == '__main__':

    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                        level=logging.INFO, datefmt='%m/%d/%Y %H:%M:%S')

    logging.info("Detecting platform")
    platform = detect_platform()

    parser = argparse.ArgumentParser(description='Run a parallel application')
    parser.add_argument('--nodes_per_exp', type=int, default=4,
                        help='Number of nodes per workflow instance')
    parser.add_argument('--problem', type=str, required=True,
                        help='Problem class')
    parser.add_argument('--max_evals', type=int, default=500,
                        help='Maximum number of evaluations')
    parser.add_argument('--exp_prefix', type=str, default='exp-',
                        help='Prefix to add to experiment instance folders')
    args = parser.parse_args()

    try:
        logging.info(f"Loading {args.problem} module")
        module_name, instance_name = args.problem.rsplit('.', 1)
        mod = importlib.import_module(args.problem)
        logging.info(f"Loading build_deephyper_problem from {args.problem} module")
        build_problem = getattr(mod, 'build_deephyper_problem')
        logging.info(f"Building problem")
        problem = build_problem()
        logging.info(f"Loading run_instance function in {args.problem}")
        run_instance = getattr(mod, 'run_instance')
    except ModuleNotFoundError as e:
        logging.critical(f'Could not load module {module_name}:')
        logging.critical(f'{e}')
        sys.exit(-1)
    except AttributeError:
        logging.critical(f'No problem {instance_name} found in module {module_name}')
        sys.exit(-1)

    logging.info("Getting list of nodes")
    nodelist = platform.get_nodelist()
    if nodelist:
        logging.info(f"Nodes are {nodelist}")
    else:
        logging.critical('No nodes could be found, please run from within an allocation')
        sys.exit(-1)
    if len(nodelist) < args.nodes_per_exp:
        logging.critical('Not enough nodes to run a single experiment')
        sys.exit(-1)
    if len(nodelist) % args.nodes_per_exp:
        logging.warning('Total number of nodes not divisible by number of nodes per exp')
        sys.exit(-1)

    build_prefix = os.environ['HEPNOS_BUILD_PREFIX']
    protocol = os.environ['HEPNOS_LIBFABRIC_PROTOCOL']
    objective_function = __make_objective_function(
        run_instance, args.exp_prefix, build_prefix, protocol, args.nodes_per_exp)

    num_tasks = int(len(nodelist)/args.nodes_per_exp)
    num_cpus_per_task = 4.0/num_tasks

    logging.info("Importing deephyper.evaluator")
    import deephyper.evaluator
    logging.info("Importing LoggerCallback from deephyper.evaluator.callback")
    from deephyper.evaluator.callback import LoggerCallback
    logging.info("Importing AMBS from deephyper.search.hps")
    from deephyper.search.hps import AMBS

    logging.info("Creating evaluator")
    QueuedRayEvaluator = deephyper.evaluator.queued(deephyper.evaluator.RayEvaluator)
    evaluator = QueuedRayEvaluator(
        deephyper.evaluator.profile(objective_function),
        num_cpus=4,
        num_cpus_per_task=num_cpus_per_task,
        callbacks=[LoggerCallback()],
        queue=nodelist,
        queue_pop_per_task=args.nodes_per_exp
    )

    logging.info("Creating AMBS instance")
    search = AMBS(problem, evaluator)

    logging.info("Starting search")
    results = search.search(max_evals=args.max_evals)
