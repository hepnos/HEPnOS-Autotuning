"""
python exec_deephyper_rf.py -m models/model-4-true-true.pkl
python exec_deephyper_rf.py -m models/model-8-true-true.pkl -tl exp/deephyper_rf/model-4-true-true-{i}/results.csv
"""
import argparse
import functools
import os
import black

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

from deephyper.evaluator import Evaluator
from deephyper.evaluator.callback import TqdmCallback
from deephyper.search.hps import AMBS

import ray

import black_box


def create_parser():
    parser = argparse.ArgumentParser(description="Create a surrogate model.")

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        required=True,
        help="Model from which to generate random points",
    )
    parser.add_argument(
        "-tl",
        "--tl-learn",
        type=str,
        default=None,
        required=False,
        help="Path to CSV file used for transfer-learning.",
    )
    return parser


def run(config, model_path):
    return black_box.run(config, model_path=model_path, with_sleep=True)


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    model_file = args.model.split("/")[-1]
    enable_pep, more_params = model_file[:-4].split("-")[2:4]
    enable_pep, more_params = enable_pep == "true", more_params == "true"

    problem = black_box.build_deephyper_problem(
        disable_pep=not (enable_pep), more_params=more_params
    )
    cols = problem.hyperparameter_names

    num_workers = 1
    ray.init(num_cpus=num_workers)

    for i in range(1, 6):
        init_file = os.path.join(HERE, "data", f"exp-DUMMY-{model_file[6:-4]}-{i}.csv")
        init_df = pd.read_csv(init_file)
        init_df = init_df[cols].iloc[:10]

        initial_points = [row.to_dict() for idx, row in init_df.iterrows()]

        timeout = 3600

        evaluator = Evaluator.create(
            run,
            method="ray",
            method_kwargs={
                "num_cpus": num_workers,
                "num_cpus_per_task": 1,
                "run_function_kwargs": {"model_path": args.model},
                "callbacks": [TqdmCallback()],
            },
        )

        print(f"Number of workers: {evaluator.num_workers}")

        if args.tl_learn:
            log_dir = f"exp/deephyper_rf/{model_file[:-4]}-tl-{i}"
            initial_points = None
        else:
            log_dir = f"exp/deephyper_rf/{model_file[:-4]}-{i}"

        search = AMBS(
            problem,
            evaluator,
            n_initial_points=10,
            initial_points=initial_points,
            log_dir=log_dir,
            random_state=42,
        )

        if args.tl_learn:
            df_path = args.tl_learn.format(i=i)
            print(f"Applying Transfer Learning from {df_path}...")
            search.fit_generative_model(df_path)

        results = search.search(timeout=timeout)
