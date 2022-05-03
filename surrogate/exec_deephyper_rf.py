"""
python exec_deephyper_rf.py -m models/model-4-true-true.pkl
python exec_deephyper_rf.py -m models/model-8-true-true.pkl -tl exp/deephyper_rf/model-4-true-true-1/results.csv
"""
import argparse
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

from deephyper.evaluator import Evaluator
from deephyper.evaluator.callback import TqdmCallback
from deephyper.search.hps import AMBS

from black_box import run, build_deephyper_problem


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
        help="Path to CSV file used for transfer-learning."
    )
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    model_file = args.model.split("/")[-1]
    enable_pep, more_params = model_file[:-4].split("-")[2:4]
    enable_pep, more_params = enable_pep == "true", more_params == "true"

    problem = build_deephyper_problem(
        disable_pep=not (enable_pep), more_params=more_params
    )
    cols = problem.hyperparameter_names

    for i in range(1, 6):
        init_file = os.path.join(HERE, "data", f"exp-DUMMY-{model_file[6:-4]}-{i}.csv")
        init_df = pd.read_csv(init_file)
        init_df = init_df[cols].iloc[:10]

        initial_points = [row.to_dict() for idx, row in init_df.iterrows()]

        max_evals = 100
        evaluator = Evaluator.create(
            run,
            method="serial",
            method_kwargs={
                "run_function_kwargs": {"model_path": args.model},
                "callbacks": [TqdmCallback(max_evals)],
            },
        )

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
            print("Applying Transfer Learning...")
            search.fit_generative_model(args.tl_learn)

        results = search.search(max_evals=max_evals)
