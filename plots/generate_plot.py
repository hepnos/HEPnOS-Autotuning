import os
import pathlib

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import yaml
import pandas as pd
import inspect
from scipy.interpolate import interp1d
from scipy.ndimage import uniform_filter1d
import numpy as np

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

width = 8
height = width / 1.618

matplotlib.rcParams.update(
    {
        "font.size": 21,
        "figure.figsize": (width, height),
        "figure.facecolor": "white",
        "savefig.dpi": 72,
        "figure.subplot.bottom": 0.125,
        "figure.edgecolor": "white",
        "xtick.labelsize": 21,
        "ytick.labelsize": 21,
    }
)

HERE = os.path.dirname(os.path.abspath(__file__))
FILE_EXTENSION = "pdf"


def yaml_load(path):
    with open(path, "r") as f:
        yaml_data = yaml.load(f, Loader=Loader)
    return yaml_data


def load_results(exp_root: str, exp_config: dict) -> dict:
    data = {}
    for exp_prefix in exp_config["data"]:
        if "rep" in exp_config["data"][exp_prefix]:
            dfs = []
            for rep in exp_config["data"][exp_prefix].get("rep"):
                exp_results_path = os.path.join(exp_root, f"{exp_prefix}-{rep}.csv")
                df = pd.read_csv(exp_results_path)
                dfs.append(df)
                data[exp_prefix] = dfs
        else:
            exp_results_path = os.path.join(exp_root, f"{exp_prefix}.csv")
            df = pd.read_csv(exp_results_path)
            data[exp_prefix] = df
    return data


@ticker.FuncFormatter
def hour_major_formatter(x, pos):
    x = float(f"{x/3600:.1f}")
    if x % 1 == 0:
        x = str(int(x))
    else:
        x = f"{x:.1f}"
    return x

@ticker.FuncFormatter
def minute_major_formatter(x, pos):
    x = float(f"{x/60:.2f}")
    if x % 1 == 0:
        x = str(int(x))
    else:
        x = f"{x:.2f}"
    return x

@ticker.FuncFormatter
def float_major_formatter(x, pos):
    x = f"{x:.0f}"
    return x


def filter_failures(df):
    if df.objective.dtype != np.float64:
        df = df[~df.objective.str.startswith("F")]
        df = df.astype({"objective": float})
    return df


def plot_scatter_multi(df, exp_config, output_dir, show):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:
            exp_dfs = exp_df
            for i, exp_df in enumerate(exp_dfs):
                exp_df = filter_failures(exp_df)
                x, y = exp_df.timestamp_end.to_numpy(), -exp_df.objective.to_numpy()
                y = np.exp(y)

                plt_kwargs = dict(
                    color=exp_config["data"][exp_name]["color"], s=10, alpha=0.5
                )
                if i == 0:
                    plt_kwargs["label"] = exp_config["data"][exp_name]["label"]

                plt.scatter(x, y, **plt_kwargs)
        else:
            exp_df = filter_failures(exp_df)
            x, y = exp_df.timestamp_end.to_numpy(), -exp_df.objective.to_numpy()
            y = np.exp(y)

            plt.scatter(
                x,
                y,
                color=exp_config["data"][exp_name]["color"],
                label=exp_config["data"][exp_name]["label"],
                s=10,
            )

    ax = plt.gca()
    ticker_freq = exp_config["t_max"] / 5
    ax.xaxis.set_major_locator(ticker.MultipleLocator(ticker_freq))
    ax.xaxis.set_major_formatter(minute_major_formatter)

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Instance run time (sec.)")
    plt.xlabel("Search time (min.)")

    if exp_config.get("ylim"):
        plt.ylim(*exp_config.get("ylim"))

    plt.xlim(0, 3600)
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    if show:
        plt.show()
    plt.close()


def only_min(values):
    res = [values[0]]
    for value in values[1:]:
        res.append(min(res[-1], value))
    return np.array(res)


def plot_objective_multi(df, exp_config, output_dir, show):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:

            exp_dfs = exp_df

            T = np.linspace(0, exp_config["t_max"], 1000)
            y_list = []
            for exp_df in exp_dfs:
                exp_df = exp_df.sort_values("timestamp_end")
                exp_df = filter_failures(exp_df)
                x, y = exp_df.timestamp_end.to_numpy(), -exp_df.objective.to_numpy()
                y = np.exp(y)
                y = only_min(y)
                f = interp1d(x, y, kind="previous", fill_value="extrapolate")
                y = f(T)
                y_list.append(y)

            num_workers = compute_num_workers(exp_name)
            y_list = np.asarray(y_list)/ num_workers * 100
            y_mean = y_list.mean(axis=0)
            y_min = y_list.min(axis=0)
            y_max = y_list.max(axis=0)

            plt.plot(
                T,
                y_mean,
                label=exp_config["data"][exp_name]["label"],
                color=exp_config["data"][exp_name]["color"],
                linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
            )
            plt.fill_between(
                T,
                y_min,
                y_max,
                facecolor=exp_config["data"][exp_name]["color"],
                alpha=0.3,
            )
        else:
            exp_df = exp_df.sort_values("timestamp_end")
            exp_df = filter_failures(exp_df)
            x, y = exp_df.timestamp_end.to_numpy(), -exp_df.objective.to_numpy()
            y = np.exp(y)
            y = only_min(y)

            plt.plot(
                x,
                y,
                label=exp_config["data"][exp_name]["label"],
                color=exp_config["data"][exp_name]["color"],
                linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
            )

    ax = plt.gca()
    ticker_freq = exp_config["t_max"] / 5
    ax.xaxis.set_major_locator(ticker.MultipleLocator(ticker_freq))
    ax.xaxis.set_major_formatter(minute_major_formatter)
    ax.yaxis.set_major_formatter(float_major_formatter)

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Instance run time (sec.)")
    plt.xlabel("Search time (min.)")

    if exp_config.get("ylim"):
        plt.ylim(*exp_config.get("ylim"))

    plt.xlim(0, 3600)
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    if show:
        plt.show()
    plt.close()


def plot_objective_multi_iter(df, exp_config, output_dir, show):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:
            exp_dfs = exp_df
            for i, exp_df in enumerate(exp_dfs):
                exp_df = exp_df.sort_values("timestamp_end")
                exp_df = filter_failures(exp_df)
                x, y = (
                    list(range(1, len(exp_df.timestamp_end.to_list()) + 1)),
                    (-exp_df.objective).to_list(),
                )
                y = np.exp(y)

                y = only_min(y)

                plt_kwargs = dict(
                    color=exp_config["data"][exp_name]["color"],
                    linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
                )

                if i == 0:
                    plt_kwargs["label"] = label = exp_config["data"][exp_name]["label"]

                plt.plot(x, y, **plt_kwargs)
        else:
            exp_df = exp_df.sort_values("timestamp_end")
            exp_df = filter_failures(exp_df)
            x, y = (
                list(range(1, len(exp_df.timestamp_end.to_list()) + 1)),
                (-exp_df.objective).to_list(),
            )
            y = np.exp(y)

            y = only_min(y)

            plt.plot(
                x,
                y,
                label=exp_config["data"][exp_name]["label"],
                color=exp_config["data"][exp_name]["color"],
                linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
            )

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(50))

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Instance run time(sec.)")
    plt.xlabel("Search Iterations")

    if exp_config.get("ylim"):
        plt.ylim(*exp_config.get("ylim"))

    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    if show:
        plt.show()
    plt.close()


def compile_profile(df):
    history = []

    for _, row in df.iterrows():
        history.append((row['timestamp_start'], 1))
        history.append((row['timestamp_end'], -1))

    history = sorted(history, key=lambda v: v[0])
    nb_workers = 0
    timestamp = [0]
    n_jobs_running = [0]
    for time, incr in history:
        nb_workers += incr
        timestamp.append(time)
        n_jobs_running.append(nb_workers)
    
    return timestamp, n_jobs_running

def compute_num_workers(exp_name):
    exp_name = exp_name.split("-")
    if "tl" == exp_name[1]:
        num_nodes_per_hepnos = int(exp_name[3])
    else:
        num_nodes_per_hepnos = int(exp_name[2])

    num_nodes = 128
    num_workers = num_nodes // num_nodes_per_hepnos
    return num_workers


def plot_utilization_multi(df, exp_config, output_dir, show):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:
            exp_dfs = exp_df
            T = np.linspace(0, exp_config["t_max"], 1000)
            y_list = []
            for exp_df in exp_dfs:
                x, y = compile_profile(exp_df)
                f = interp1d(x, y, kind="previous", fill_value="extrapolate")
                y = f(T)
                y_list.append(y)

            num_workers = compute_num_workers(exp_name)
            y_list = np.asarray(y_list)/ num_workers * 100
            y_mean = y_list.mean(axis=0)
            y_min = y_list.min(axis=0)
            y_max = y_list.max(axis=0)

            win_size = 10
            y_mean = uniform_filter1d(y_mean, size=win_size)
            y_min = uniform_filter1d(y_min, size=win_size)
            y_max = uniform_filter1d(y_max, size=win_size)

            plt_kwargs = dict(
                color=exp_config["data"][exp_name]["color"],
                linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
            )

            plt_kwargs["label"] = exp_config["data"][exp_name]["label"]

            plt.plot(T, y_mean, **plt_kwargs)
            plt.fill_between(
                T,
                y_min,
                y_max,
                alpha=0.25,
                color=exp_config["data"][exp_name]["color"],
            )
        else:
            x, y = compile_profile(exp_df)

            num_workers = compute_num_workers(exp_name)
            y = np.asarray(y) / num_workers * 100

            plt.step(
                x,
                y,
                where="pre",
                label=exp_config["data"][exp_name]["label"],
                color=exp_config["data"][exp_name]["color"],
                linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
            )

    ax = plt.gca()
    ticker_freq = exp_config["t_max"] / 5
    ax.xaxis.set_major_locator(ticker.MultipleLocator(ticker_freq))
    ax.xaxis.set_major_formatter(minute_major_formatter)

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Workers Evaluating $f(x)$ (%)")
    plt.xlabel("Search time (min.)")
    plt.xlim(0, 3600)
    plt.ylim(0,100)

    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    if show:
        plt.show()
    plt.close()


def generate_figures(config):

    exp_root = config["root"]
    figures_dir = os.path.join(HERE, "figures")
    show = config.get("show", False)

    for exp_num, exp_config in config["experiments"].items():
        exp_dirname = str(exp_num)
        output_dir = os.path.join(figures_dir, exp_dirname)

        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

        df = load_results(exp_root, exp_config)

        plot_functions = [
            plot_scatter_multi,
            plot_objective_multi,
            # plot_objective_multi_iter,
            plot_utilization_multi,
        ]

        for plot_func in plot_functions:
            plot_func(df, exp_config, output_dir, show)


if __name__ == "__main__":
    yaml_path = os.path.join(HERE, "plot.yaml")
    config = yaml_load(yaml_path)
    generate_figures(config)
    print("Done!")
