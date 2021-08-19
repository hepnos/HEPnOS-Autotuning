import os
import ray
import pandas as pd

from hepnos_theta.run import run
from hepnos_theta.problem import Problem

settings = {
    "num_cpus": 0.25,
    "num_samples": 50
}
# settings = {
#     "num_cpus": 1,
#     "num_samples": 5
# } # debug


ray.init(address="auto")

run_func = ray.remote(num_cpus=settings["num_cpus"])(run)

configs = Problem.space.sample_configuration(settings["num_samples"])
configs = [config.get_dictionary() for config in configs]

os.environ["DH_HEPNOS_ENABLE_PEP"] = "0"
solutions = ray.get([run_func.remote(c) for c in configs])
results = []
for conf, sol in zip(configs, solutions):
    conf = conf.copy()
    conf["objective"] = sol
    results.append(conf)
df1 = pd.DataFrame(results)
df1.to_csv("results-no-pep.csv")

os.environ["DH_HEPNOS_ENABLE_PEP"] = "1"
solutions = ray.get([run_func.remote(c) for c in configs])
results = []
for conf, sol in zip(configs, solutions):
    conf = conf.copy()
    conf["objective"] = sol
    results.append(conf)
df2 = pd.DataFrame(results)
df2.to_csv("results-pep.csv")