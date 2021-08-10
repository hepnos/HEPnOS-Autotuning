from deephyper.problem import HpProblem

Problem = HpProblem(seed=2021)

# 1. step
Problem.add_hyperparameter((0, 31), "hepnos_num_threads")
Problem.add_hyperparameter((1, 10), "hepnos_num_databases")
Problem.add_hyperparameter([True, False], "busy_spin")
Problem.add_hyperparameter([True, False], "loader_progress_thread")
Problem.add_hyperparameter((1, 2048, "log-uniform"), "loader_batch_size")

# 2. step: when "enable_step == True"
Problem.add_hyperparameter((1, 31), "pep_num_threads")
Problem.add_hyperparameter((8, 1024, "log-uniform"), "pep_ibatch_size")
Problem.add_hyperparameter((8, 1024, "log-uniform"), "pep_obatch_size")
Problem.add_hyperparameter([True, False], "pep_use_preloading")
Problem.add_hyperparameter((1, 64), "pep_pes_per_node")
Problem.add_hyperparameter((1, 64), "pep_cores_per_pe")



if __name__ == "__main__":
    print(Problem)