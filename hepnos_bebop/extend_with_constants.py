import pandas as pd

HP_DEFAULT_VALUES = {
    "hepnos_num_threads": 31,
    "hepnos_num_databases": 1,
    "busy_spin": False,
    "loader_progress_thread": False,
    "loader_batch_size": 1024,
    "enable_pep": False,
    "pep_num_threads": 31,
    "pep_ibatch_size": 32,
    "pep_obatch_size": 32,
    "pep_use_preloading": False,
    "pep_pes_per_node": 16,
    "pep_cores_per_pe": 4
}

def transform_with_constants(source_csv: str, output_csv: str, hp_list: list, hp_default: dict):
    source_df = pd.read_csv(source_csv)

    for hp in hp_list:
        if not(hp in source_df.columns):
            source_df[hp] = hp_default[hp] # create new column with default value

    source_df.to_csv(output_csv)



if __name__ == "__main__":
    source_csv = "exp-1/results.csv"
    output_csv = "exp/results.csv"

    from problem import Problem
    hp_list = Problem.space.get_hyperparameter_names()

    transform_with_constants(source_csv, output_csv, hp_list, HP_DEFAULT_VALUES)


