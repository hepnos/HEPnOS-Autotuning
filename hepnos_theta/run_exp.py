"""
python -m hepnos_theta.run_exp -w exp/exp-test -q debug-cache-quad -t 60 -A radix-io -n 8 --nodes-per-task 4 -as ./SetUpEnv.sh --run hepnos_theta.run.run --problem hepnos_theta.problem.Problem --fit-search-space exp/
"""
import os
import argparse
import pathlib
import stat
from jinja2 import Template

HERE = os.path.dirname(os.path.abspath(__file__))
JOB_TEMPLATE = os.path.join(HERE, "job.qsub.tmpl")


def run(w, q, A, t, n, enable_pep, nodes_per_task, activation_script, run,
        problem, fit_surrogate, fit_search_space):

    num_dh_workers = n // nodes_per_task

    enable_pep = int(enable_pep)

    # for transfer learning
    if fit_surrogate:
        fit_surrogate = os.path.abspath(fit_surrogate)

    if fit_search_space:
        fit_search_space = os.path.abspath(fit_search_space)

    # create exp directory
    exp_dir = os.path.abspath(w)
    pathlib.Path(exp_dir).mkdir(parents=True, exist_ok=False)

    activation_script = os.path.abspath(activation_script)

    # load template
    with open(JOB_TEMPLATE, "r") as f:
        job_template = Template(f.read())

    submission_path = os.path.join(w, "job.qsub")
    with open(submission_path, "w") as fp:
        fp.write(
            job_template.render(q=q,
                                A=A,
                                t=t,
                                n=n,
                                enable_pep=enable_pep,
                                nodes_per_task=nodes_per_task,
                                num_dh_workers=num_dh_workers,
                                activation_script=activation_script,
                                exp_dir=exp_dir,
                                run=run,
                                problem=problem,
                                fit_surrogate=fit_surrogate,
                                fit_search_space=fit_search_space))

    # add executable rights
    st = os.stat(submission_path)
    os.chmod(submission_path, st.st_mode | stat.S_IEXEC)

    # Job submission
    os.chdir(exp_dir)
    print("Performing job submission...")
    cmd = f"qsub job.qsub"
    # os.system(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HEPnOS experiment')
    parser.add_argument('-w',
                        required=True,
                        type=str,
                        help="Name of the experiment.")
    parser.add_argument('-q', required=True, type=str, help="Queue name.")
    parser.add_argument('-A',
                        default="radix-io",
                        type=str,
                        help="Project name.")
    parser.add_argument('-t',
                        required=True,
                        type=str,
                        help="Duration of the experiment.")
    parser.add_argument('-n',
                        required=True,
                        type=int,
                        help="Number of nodes for the total allocation.")
    parser.add_argument('--enable-pep',
                        action='store_true',
                        default=False,
                        help='enable PEP benchmark')
    parser.add_argument('--nodes-per-task',
                        type=int,
                        default=None,
                        help='Number of nodes to use per task.')
    parser.add_argument(
        '-as',
        '--activation-script',
        required=True,
        type=str,
        help="Path to the script activation the conda environment.")
    parser.add_argument('--run', required=True, type=str)
    parser.add_argument('--problem', required=True, type=str)
    parser.add_argument('--fit-surrogate', required=False, type=str, default="")
    parser.add_argument('--fit-search-space', required=False, type=str, default="")
    args = parser.parse_args()
    run(**vars(args))