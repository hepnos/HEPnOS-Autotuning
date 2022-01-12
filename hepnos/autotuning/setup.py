import os
import glob
import sys
import argparse
import pathlib
import stat
import logging
import importlib
from jinja2 import Template
from .linux import jobs

HERE = os.path.dirname(os.path.abspath(__file__))


def submit(w, q, A, t, n, step, nodes_per_task,
           activation_script, run, problem,
           fit_surrogate, fit_search_space,
           transfer_learning_strategy,
           transfer_learning_epsilon):

    w = w.encode("ascii").decode("ascii")
    num_dh_workers = n // nodes_per_task # N_T
    num_cpus_driver = 4 # N_R
    num_cpus_per_task = num_cpus_driver / num_dh_workers # N_{R/T}
    step = int(step)

    platform = os.getenv('HEPNOS_EXP_PLATFORM')
    if platform is None:
        logging.critical('Could not get platform from HEPNOS_EXP_PLATFORM variable.')
        sys.exit(-1)

    # for transfer learning
    if fit_surrogate:
        fit_surrogate = os.path.abspath(fit_surrogate)

    if fit_search_space:
        fit_search_space = os.path.abspath(fit_search_space)

    # find activation script
    activation_script = os.path.abspath(activation_script)
    if not os.path.isfile(activation_script):
        logging.critical(f'Activation script {activation_script} not found, aborting.')
        sys.exit(-1)

    # import platform-specific module
    try:
        importlib.import_module('hepnos.autotuning.'+platform+'.jobs')
    except ModuleNotFoundError:
        loggin.critical(f'Could not find module corresponding to {platform}')
        sys.exit(-1)

    # create exp directory
    exp_dir = os.path.abspath(w)
    if os.path.isdir(exp_dir):
        logging.critical(f'Directory {w} already exists, aborting.')
        sys.exit(-1)
    pathlib.Path(exp_dir).mkdir(parents=True, exist_ok=False)

    # find the job template
    job_template = HERE+'/job.tmpl'
    job_file = 'job.sh'

    # load template
    with open(job_template, "r") as f:
        job_template = Template(f.read())

    submission_path = os.path.join(w, job_file)
    with open(submission_path, "w") as fp:
        fp.write(jobs.generate_preamble(A=A, t=t, n=n, q=q)+'\n')
        fp.write(
            job_template.render(
                hepnos_exp_step=step,
                nodes_per_task=nodes_per_task,
                num_cpus_driver=num_cpus_driver,
                num_cpus_per_task=num_cpus_per_task,
                activation_script=activation_script,
                exp_dir=exp_dir,
                run=run,
                problem=problem,
                fit_surrogate=fit_surrogate,
                fit_search_space=fit_search_space,
                transfer_learning_strategy=transfer_learning_strategy,
                transfer_learning_epsilon=transfer_learning_epsilon))

    # add executable rights
    st = os.stat(submission_path)
    os.chmod(submission_path, st.st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HEPnOS experiment')
    parser.add_argument('-w', required=True, type=str,
        help="Directory to create for the experiment.")
    parser.add_argument('-q', required=False, default='', type=str,
        help="Queue name.")
    parser.add_argument('-A', required=False, default='', type=str,
        help="Project/allocation name.")
    parser.add_argument('-t', required=False, default='1:00:00', type=str,
        help="Maximum duration of the experiment.")
    parser.add_argument('-n', required=True, type=int,
        help="Number of nodes for the total allocation.")
    parser.add_argument('--step', type=int, default=1,
        help='HEPnOS experiment step.')
    parser.add_argument('--nodes-per-task', type=int, default=None,
        help='Number of nodes to use per task.')
    parser.add_argument('-as', '--activation-script', required=True, type=str,
        help="Path to the script activation the conda environment.")
    parser.add_argument('--run', required=False, type=str,
        default='hepnos.autotuning.run',
        help="Python function to run in each task (fully qualified).")
    parser.add_argument('--problem', required=False, type=str,
        default='hepnos.autotuning.problem',
        help="Problem/parameter-space description (fully qualified).")
    parser.add_argument('--fit-surrogate', required=False, type=str, default="",
        help="""Fit the surrogate model of the search from a checkpointed Dataframe.""")
    parser.add_argument('--fit-search-space', required=False, type=str, default="",
        help="""CSV file corresponding to a previous search used to initialize
        the sampling prior of compatible hyperparameters of the current search space.""")
    parser.add_argument('--transfer-learning-strategy', required=False,
        type=str, default="best", choices=["best", "epsilon"],
        help="Transfer learning strategy.")
    parser.add_argument('--transfer-learning-epsilon', required=False,
        type=float, default=1.0,
        help="Transfer learning epsilon.")
    args = parser.parse_args()
    submit(**vars(args))
