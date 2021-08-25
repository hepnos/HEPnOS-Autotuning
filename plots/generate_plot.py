import os
import pathlib

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import yaml
import pandas as pd
import inspect
from scipy import stats
import numpy as np

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

width = 8
height = width / 1.618

matplotlib.rcParams.update({
    'font.size': 21,
    'figure.figsize': (width, height),
    'figure.facecolor': 'white',
    'savefig.dpi': 72,
    'figure.subplot.bottom': 0.125,
    'figure.edgecolor': 'white',
    'xtick.labelsize': 21,
    'ytick.labelsize': 21
})

HERE = os.path.dirname(os.path.abspath(__file__))
FILE_EXTENSION = "png"


def yaml_load(path):
    with open(path, "r") as f:
        yaml_data = yaml.load(f, Loader=Loader)
    return yaml_data


def load_results(exp_root: str, exp_config: dict) -> dict:
    data = {}
    for exp_folder in exp_config["data"]:
        if "rep" in exp_config["data"][exp_folder]:
            dfs = []
            for rep in exp_config["data"][exp_folder].get("rep"):
                exp_results_path = os.path.join(exp_root,
                                                f"{exp_folder}-rep{rep}",
                                                "results.csv")
                df = pd.read_csv(exp_results_path)
                dfs.append(df)
                data[exp_folder] = dfs
        else:
            exp_results_path = os.path.join(exp_root, exp_folder,
                                            "results.csv")
            df = pd.read_csv(exp_results_path)
            data[exp_folder] = df
    return data


@ticker.FuncFormatter
def hour_major_formatter(x, pos):
    x = float(f"{x/3600:.1f}")
    if x % 1 == 0:
        x = str(int(x))
    else:
        x = f"{x:.1f}"
    return x


def plot_scatter_multi(df, exp_config, output_dir):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:
            exp_dfs = exp_df
            for i, exp_df in enumerate(exp_dfs):
                x, y = exp_df.elapsed_sec.to_numpy(
                ), -exp_df.objective.to_numpy()

                plt_kwargs = dict(color=exp_config["data"][exp_name]["color"],
                                  s=10,
                                  alpha=0.5)
                if i == 0:
                    plt_kwargs["label"] = exp_config["data"][exp_name]["label"]

                plt.scatter(x, y, **plt_kwargs)
        else:
            x, y = exp_df.elapsed_sec.to_numpy(), -exp_df.objective.to_numpy()

            plt.scatter(x,
                        y,
                        color=exp_config["data"][exp_name]["color"],
                        label=exp_config["data"][exp_name]["label"],
                        s=10)

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(900))
    ax.xaxis.set_major_formatter(hour_major_formatter)

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Instance run time (sec)")
    plt.xlabel("Search time (hour)")

    if exp_config.get("ylim"):
        plt.ylim(*exp_config.get("ylim"))

    plt.xlim(0, 3600)
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()


def only_min(values):
    res = [values[0]]
    for value in values[1:]:
        res.append(min(res[-1], value))
    return np.array(res)


def plot_objective_multi(df, exp_config, output_dir):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:

            exp_dfs = exp_df

            times = np.unique(
                np.concatenate([df.elapsed_sec.to_numpy() for df in exp_dfs],
                               axis=0))

            series = []
            for exp_df in exp_dfs:

                exp_df = exp_df.sort_values("elapsed_sec")
                x, y = exp_df.elapsed_sec.to_numpy(
                ), -exp_df.objective.to_numpy()
                y = only_min(y)

                s = pd.Series(data=y, index=x)
                s = s.reindex(times).fillna(method="ffill")
                series.append(s)

            array = np.array([s.to_numpy() for s in series])
            loc = np.nanmean(array, axis=0)
            scale = np.nanstd(array, axis=0)

            plt.plot(
                times,
                loc,
                label=exp_config["data"][exp_name]["label"],
                color=exp_config["data"][exp_name]["color"],
                linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
            )
            plt.fill_between(times,
                             loc - 1 * scale,
                             loc + 1 * scale,
                             facecolor=exp_config["data"][exp_name]["color"],
                             alpha=0.3)
        else:
            exp_df = exp_df.sort_values("elapsed_sec")
            x, y = exp_df.elapsed_sec.to_numpy(), -exp_df.objective.to_numpy()
            y = only_min(y)

            plt.plot(x,
                     y,
                     label=exp_config["data"][exp_name]["label"],
                     color=exp_config["data"][exp_name]["color"],
                     linestyle=exp_config["data"][exp_name].get(
                         "linestyle", "-"))

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(900))
    ax.xaxis.set_major_formatter(hour_major_formatter)

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Instance run time (sec)")
    plt.xlabel("Search time (hour)")

    if exp_config.get("ylim"):
        plt.ylim(*exp_config.get("ylim"))

    plt.xlim(0, 3600)
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()


def plot_objective_multi_iter(df, exp_config, output_dir):
    output_file_name = f"{inspect.stack()[0][3]}.{FILE_EXTENSION}"
    output_path = os.path.join(output_dir, output_file_name)

    plt.figure()

    for exp_name, exp_df in df.items():

        if "rep" in exp_config["data"][exp_name]:
            exp_dfs = exp_df
            for exp_df in exp_dfs:
                exp_df = exp_df.sort_values("elapsed_sec")
                x, y = list(range(1,
                                  len(exp_df.elapsed_sec.to_list()) +
                                  1)), (-exp_df.objective).to_list()

                y = only_min(y)

                plt.plot(
                    x,
                    y,
                    label=exp_config["data"][exp_name]["label"],
                    color=exp_config["data"][exp_name]["color"],
                    linestyle=exp_config["data"][exp_name].get(
                        "linestyle", "-"),
                )
        else:
            exp_df = exp_df.sort_values("elapsed_sec")
            x, y = list(range(1,
                              len(exp_df.elapsed_sec.to_list()) +
                              1)), (-exp_df.objective).to_list()

            y = only_min(y)

            plt.plot(x,
                     y,
                     label=exp_config["data"][exp_name]["label"],
                     color=exp_config["data"][exp_name]["color"],
                     linestyle=exp_config["data"][exp_name].get(
                         "linestyle", "-"))

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(50))

    if exp_config.get("title"):
        plt.title(exp_config.get("title"))

    plt.legend()
    plt.ylabel("Experiment Duration (sec.)")
    plt.xlabel("#Evaluation")

    if exp_config.get("ylim"):
        plt.ylim(*exp_config.get("ylim"))

    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()


def generate_figures(config):

    exp_root = config["root"]
    figures_dir = os.path.join(HERE, "figures")

    for exp_num, exp_config in config["experiments"].items():
        exp_dirname = str(exp_num)
        output_dir = os.path.join(figures_dir, exp_dirname)

        pathlib.Path(output_dir).mkdir(parents=False, exist_ok=True)

        df = load_results(exp_root, exp_config)

        plot_scatter_multi(df, exp_config, output_dir)
        plot_objective_multi(df, exp_config, output_dir)
        plot_objective_multi_iter(df, exp_config, output_dir)


if __name__ == "__main__":
    yaml_path = os.path.join(HERE, "plot.yaml")
    config = yaml_load(yaml_path)
    generate_figures(config)
    print("Done!")
