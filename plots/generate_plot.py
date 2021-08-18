import os
import pathlib

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
            for exp_df in exp_dfs:
                x, y = exp_df.elapsed_sec.to_numpy(
                ), -exp_df.objective.to_numpy()
                plt.scatter(x,
                            y,
                            label=exp_config["data"][exp_name]["label"],
                            s=10)
        else:
            x, y = exp_df.elapsed_sec.to_numpy(), -exp_df.objective.to_numpy()
            # z = stats.zscore(y)
            # z_threshold = 3
            # selection = np.where(z <= z_threshold)
            # x, y = x[selection], y[selection]
            plt.scatter(x,
                        y,
                        label=exp_config["data"][exp_name]["label"],
                        s=10)

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(900))
    ax.xaxis.set_major_formatter(hour_major_formatter)

    plt.title(exp_config["title"])
    plt.legend()
    plt.ylabel("Experiment Duration (sec.)")
    plt.xlabel("Run Time (hour)")
    plt.ylim(0, 300)
    plt.grid()
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
            for exp_df in exp_dfs:
                exp_df = exp_df.sort_values("elapsed_sec")
                x, y = exp_df.elapsed_sec.to_numpy(), -exp_df.objective.to_numpy()

                y = only_min(y)

                plt.plot(x, y,
                    label=exp_config["data"][exp_name]["label"],
                    color=exp_config["data"][exp_name]["color"],
                    linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
                    )
        else:
            exp_df = exp_df.sort_values("elapsed_sec")
            x, y = exp_df.elapsed_sec.to_numpy(), -exp_df.objective.to_numpy()
            y = only_min(y)

            plt.plot(x, y, label=exp_config["data"][exp_name]["label"],
                    color=exp_config["data"][exp_name]["color"],
                    linestyle=exp_config["data"][exp_name].get("linestyle", "-"))

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(900))
    ax.xaxis.set_major_formatter(hour_major_formatter)

    plt.title(exp_config["title"])
    plt.legend()
    plt.ylabel("Experiment Duration (sec.)")
    plt.xlabel("Run Time (hour)")
    plt.ylim(30, 100)
    plt.grid()
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
                x, y = list(range(1, len(exp_df.elapsed_sec.to_list())+1)), (-exp_df.objective).to_list()

                y = only_min(y)

                plt.plot(x, y,
                    label=exp_config["data"][exp_name]["label"],
                    color=exp_config["data"][exp_name]["color"],
                    linestyle=exp_config["data"][exp_name].get("linestyle", "-"),
                    )
        else:
            exp_df = exp_df.sort_values("elapsed_sec")
            x, y = list(range(1, len(exp_df.elapsed_sec.to_list())+1)), (-exp_df.objective).to_list()

            y = only_min(y)

            plt.plot(x, y, label=exp_config["data"][exp_name]["label"],
                    color=exp_config["data"][exp_name]["color"],
                    linestyle=exp_config["data"][exp_name].get("linestyle", "-"))

    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    # ax.xaxis.set_major_formatter(hour_major_formatter)

    plt.title(exp_config["title"])
    plt.legend()
    plt.ylabel("Experiment Duration (sec.)")
    plt.xlabel("#Evaluation")
    plt.ylim(30, 100)
    plt.xlim(0, 150)
    plt.grid()
    plt.savefig(output_path)
    plt.show()


def generate_figures(config):

    exp_root = config["root"]
    figures_dir = os.path.join(HERE, "figures")

    for exp_num, exp_config in config["experiments"].items():
        exp_title = exp_config["title"]
        exp_dirname = str(exp_num) + "-" + exp_title.lower().replace(" ", "_")
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