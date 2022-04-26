import argparse
import pickle
import glob
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def create_parser():
    parser = argparse.ArgumentParser(description="Create a surrogate model.")

    parser.add_argument(
        "-i", "--input_dir", type=str, default="exp-DUMMY-4-false-false/", help="Path to the *.csv file."
    )

    return parser


def main(args):

    # load the data
    
    all_files = glob.glob(args.input_dir + "/*.csv")
    li = []
    for filename in all_files:
        print(f"Loading: {filename}")
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)
    real_data = pd.concat(li, axis=0, ignore_index=True)

    # ignore failures
    real_data = real_data[~real_data.objective.str.startswith("F")]
    real_data = real_data.astype({"objective": float})

    real_data[['objective']] = real_data[['objective']].astype(float)

    real_data = real_data.drop(
        columns=["job_id","timestamp_submit","timestamp_gather","timestamp_start","timestamp_end","dequed"]
    )

    # model fitting
    cat_vars = [
        "busy_spin",
        "hepnos_pool_type",
        "hepnos_progress_thread",
        "loader_progress_thread",
    ]
    num_vars = [
        "hepnos_num_event_databases",	
        "hepnos_num_product_databases",	
        "hepnos_num_providers",	
        "hepnos_num_rpc_threads",	
        "hepnos_pes_per_node",
        "loader_batch_size",
        "loader_pes_per_node",
    ]
    response_vars = ["objective"]

    num_pipeline = Pipeline(
        [
            ("std_scaler", StandardScaler()),
        ]
    )

    data_pipeline = ColumnTransformer(
        [
            ("response", num_pipeline, response_vars),
            ("numerical", num_pipeline, num_vars),
            ("categorical", OneHotEncoder(sparse=False), cat_vars),
        ]
    )

    data_pipeline_model = data_pipeline.fit(real_data)

    preprocessed_data = data_pipeline_model.transform(real_data)

    X_train, X_test, y_train, y_test = train_test_split(
        preprocessed_data[:, 1:],
        preprocessed_data[:, [0]],
        test_size=0.10,
        random_state=42,
    )

    regr = RandomForestRegressor()
    regr.fit(X_train,y_train)
    preds = regr.predict(X_test)
    r2 = r2_score(y_test[:,0],preds)
    print(f"training objective {r2=}")

    preprocessed_data = data_pipeline_model.transform(real_data)
    preds = regr.predict(preprocessed_data[:, 1:])
    r2 = r2_score(preprocessed_data[:, 0], preds)
    print(f"full data objective {r2=}")

    saved_pipeline = {
        "data": data_pipeline_model,
        "model": regr,
    }
    with open(args.input_dir+"/surrogate.pkl", "wb") as f:
        pickle.dump(saved_pipeline, f)

if __name__ == "__main__":
    parser = create_parser()

    args = parser.parse_args()

    main(args)
