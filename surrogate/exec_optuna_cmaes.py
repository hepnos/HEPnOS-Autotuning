"""
python exec_deephyper -m models/model-4-true-true.pkl
"""
import argparse
import os
import functools
import pathlib

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

import optuna
from optuna.samplers import CmaEsSampler

from black_box import run


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
    return parser


def suggest(trial, disable_pep, more_params) -> dict:
    """Fill either an argparse parser or a DeepHyper problem using
    the provided add_parameter callback."""

    config = {}
    config["busy_spin"] = trial.suggest_categorical("busy_spin", [True, False])
    config["hepnos_progress_thread"] = trial.suggest_categorical(
        "hepnos_progress_thread", [True, False]
    )
    config["hepnos_num_rpc_threads"] = trial.suggest_int(
        "hepnos_num_rpc_threads", 0, 63
    )
    config["hepnos_num_event_databases"] = trial.suggest_int(
        "hepnos_num_event_databases", 1, 16
    )

    config["hepnos_num_product_databases"] = trial.suggest_int(
        "hepnos_num_product_databases", 1, 16
    )
    config["hepnos_num_providers"] = trial.suggest_int("hepnos_num_providers", 1, 32)
    config["hepnos_pool_type"] = trial.suggest_categorical(
        "hepnos_pool_type", ["fifo", "fifo_wait"]
    )
    config["hepnos_pes_per_node"] = trial.suggest_categorical(
        "hepnos_pes_per_node", [1, 2, 4, 8, 16, 32]
    )
    config["loader_progress_thread"] = trial.suggest_categorical(
        "loader_progress_thread", [True, False]
    )
    config["loader_batch_size"] = trial.suggest_int(
        "loader_batch_size", 1, 2048, log=True
    )
    config["loader_pes_per_node"] = trial.suggest_categorical(
        "loader_pes_per_node", [1, 2, 4, 8, 16]
    )

    if more_params:
        config["loader_async"] = trial.suggest_categorical(
            "loader_async", [True, False]
        )
        config["loader_async_threads"] = trial.suggest_int(
            "loader_async_threads", 1, 63, log=True
        )

    if disable_pep:
        return config

    config["pep_progress_thread"] = trial.suggest_categorical(
        "pep_progress_thread", [True, False]
    )
    config["pep_num_threads"] = trial.suggest_int("pep_num_threads", 1, 31)
    config["pep_ibatch_size"] = trial.suggest_int("pep_ibatch_size", 8, 1024, log=True)
    config["pep_obatch_size"] = trial.suggest_int("pep_obatch_size", 8, 1024, log=True)
    config["pep_pes_per_node"] = trial.suggest_categorical(
        "pep_pes_per_node", [1, 2, 4, 8, 16, 32]
    )

    if more_params:
        config["pep_no_preloading"] = trial.suggest_categorical(
            "pep_no_preloading", [True, False]
        )
        config["pep_no_rdma"] = trial.suggest_categorical("pep_no_rdma", [True, False])

    return config


def run_optuna(trial, model_path, disable_pep, more_params):
    config = suggest(trial, disable_pep, more_params)

    y = run(config, model_path, maximise=False)

    return y["objective"]


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    model_file = args.model.split("/")[-1]
    enable_pep, more_params = model_file[:-4].split("-")[2:4]
    enable_pep, more_params = enable_pep == "true", more_params == "true"

    objective = functools.partial(
        run_optuna,
        model_path=args.model,
        disable_pep=not (enable_pep),
        more_params=more_params,
    )

    for i in range(1, 6):
        init_file = os.path.join(HERE, "data", f"exp-DUMMY-{model_file[6:-4]}-{i}.csv")
        init_df = pd.read_csv(init_file).drop(columns="job_id,objective,timestamp_submit,timestamp_gather,timestamp_start,timestamp_end,dequed".split(","))
        init_df = init_df.iloc[:10]
        initial_points = [row.to_dict() for idx, row in init_df.iterrows()]

        # optuna
        study = optuna.create_study(sampler=CmaEsSampler(seed=42))
        print(f"Sampler is {study.sampler.__class__.__name__}")

        for init_p in initial_points:
            study.enqueue_trial(init_p)
        study.optimize(objective, n_trials=100, show_progress_bar=True)

        df = study.trials_dataframe()
        df = df.rename(columns={"value": "objective"})
        print(df)

        dir_path = f"exp/optuna_cmaes/{model_file[:-4]}-{i}"
        pathlib.Path(dir_path).mkdir(parents=False, exist_ok=True)

        df.to_csv(os.path.join(dir_path, "results.csv"))

