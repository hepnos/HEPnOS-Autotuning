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
        print(filename)
        df = pd.read_csv(filename, index_col=None, header=0)
        print(df)
        li.append(df)
    real_data = pd.concat(li, axis=0, ignore_index=True)

    print(real_data)
    real_data = real_data.replace('F10001', 100.0)
    real_data = real_data.replace('F10003', 200.0)
    #print(real_data[['objective']].describe())
    real_data[['objective']] = real_data[['objective']].astype(float)
    print(real_data[['objective']].describe())


    #real_data.to_csv('test.csv')
    #sys.exit(0)
    #real_data = pd.read_csv(args.input, index_col=0)
    real_data["elapsed"] = real_data["timestamp_end"] - real_data["timestamp_start"]

    real_data = real_data.drop(
        columns=["job_id","timestamp_submit","timestamp_gather","timestamp_start","timestamp_end","dequed"]
    )

    real_df = real_data
    real_df_cut = real_df

    print(real_df.columns)
    # preprocessing
    quantiles = np.quantile(
        real_df_cut["objective"].values, [0.10, 0.25, 0.50, 0.75, 0.90]
    )
    real_df_cut_0 = real_df_cut[real_df_cut.objective >= quantiles[4]]
    real_df_cut_1 = real_df_cut[
        (real_df_cut["objective"] >= quantiles[3])
        & (real_df_cut["objective"] < quantiles[4])
    ]
    real_df_cut_2 = real_df_cut[
        (real_df_cut["objective"] >= quantiles[2])
        & (real_df_cut["objective"] < quantiles[3])
    ]
    real_df_cut_3 = real_df_cut[
        (real_df_cut["objective"] >= quantiles[1])
        & (real_df_cut["objective"] < quantiles[2])
    ]
    real_df_cut_4 = real_df_cut[
        (real_df_cut["objective"] >= quantiles[0])
        & (real_df_cut["objective"] < quantiles[1])
    ]
    real_df_cut_5 = real_df_cut[(real_df_cut["objective"] < quantiles[0])]

    nresamp = 200

    real_df_cut_list = []
    if real_df_cut_0.shape[0] > 0:
        real_df_cut_0_r = real_df_cut_0.sample(nresamp, replace=True)
        real_df_cut_list.append(real_df_cut_0_r)
    
    if real_df_cut_1.shape[0] > 0:
        real_df_cut_1_r = real_df_cut_1.sample(nresamp, replace=True)
        real_df_cut_list.append(real_df_cut_1_r)
    
    if real_df_cut_2.shape[0] > 0:
        real_df_cut_2_r = real_df_cut_2.sample(nresamp, replace=True)
        real_df_cut_list.append(real_df_cut_2_r)
    
    if real_df_cut_3.shape[0] > 0:
        real_df_cut_3_r = real_df_cut_3.sample(nresamp, replace=True)
        real_df_cut_list.append(real_df_cut_3_r)
    
    if real_df_cut_4.shape[0] > 0:
        real_df_cut_4_r = real_df_cut_4.sample(nresamp, replace=True)
        real_df_cut_list.append(real_df_cut_4_r)
    
    if real_df_cut_5.shape[0] > 0:
        real_df_cut_5_r = real_df_cut_5.sample(nresamp, replace=True)
        real_df_cut_list.append(real_df_cut_5_r)

    real_df_cut_r = pd.concat(real_df_cut_list)

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
    response_vars = ["objective", "elapsed"]

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

    data_pipeline_model = data_pipeline.fit(real_df_cut_r)

    preprocessed_data = data_pipeline_model.transform(real_df_cut_r)

    X_train, X_test, y_train, y_test = train_test_split(
        preprocessed_data[:, 2:],
        preprocessed_data[:, [0, 1]],
        test_size=0.10,
        random_state=42,
    )

    regr = RandomForestRegressor()
    regr.fit(X_train,y_train)
    preds = regr.predict(X_test)
    r2 = r2_score(y_test[:,0],preds[:,0])
    print(f"training objective {r2=}")
    r2 = r2_score(y_test[:,1],preds[:,1])
    print(f"training elapsed   {r2=}")

    preprocessed_data = data_pipeline_model.transform(real_df_cut_r)
    preds = regr.predict(preprocessed_data[:, 2:])
    r2 = r2_score(preprocessed_data[:, 0],preds[:,0])
    print(f"full data objective {r2=}")

    r2 = r2_score(preprocessed_data[:, 1],preds[:,1])
    print(f"full data elapsed   {r2=}")

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
