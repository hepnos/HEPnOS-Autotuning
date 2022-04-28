import argparse

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
        "-o",
        "--output",
        type=str,
        default=None,
        required=True,
        help="Path where to store the results",
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

    max_evals = 10_000
    evaluator = Evaluator.create(
        run,
        method="serial",
        method_kwargs={
            "run_function_kwargs": {"model_path": args.model},
            "callbacks": [TqdmCallback(max_evals)],
        },
    )
    search = AMBS(
        problem,
        evaluator,
        surrogate_model="DUMMY",
        log_dir=args.output,
        random_state=42,
    )

    results = search.search(max_evals=max_evals)
