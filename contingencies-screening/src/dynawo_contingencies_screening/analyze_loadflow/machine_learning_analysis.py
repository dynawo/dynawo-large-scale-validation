import os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from numpy import mean, std
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from dynawo_contingencies_screening.analyze_loadflow import human_analysis

STD_TAP_VALUE = 20


def convert_dict_to_df(contingencies_dict, elements_dict, tap_changers, predicted_score=False):
    # Convert and compute the result dictionaries to a usable dataframe for training and
    # predicting with the machine learning model.

    contingencies_df = {
        "NUM": [],
        "NAME": [],
        "MIN_VOLT": [],
        "MAX_VOLT": [],
        "MAX_FLOW": [],
        "N_ITER": [],
        "AFFECTED_ELEM": [],
        "CONSTR_GEN_Q": [],
        "CONSTR_GEN_U": [],
        "CONSTR_VOLT": [],
        "CONSTR_FLOW": [],
        "RES_NODE": [],
        "COEF_REPORT": [],
    }

    if tap_changers:
        contingencies_df["TAP_CHANGERS"] = []

    if predicted_score:
        contingencies_df["PREDICTED_SCORE"] = []

    error_contg = {}

    for key in contingencies_dict.keys():
        value_min_voltages = human_analysis.calc_diff_volt(
            contingencies_dict[key]["min_voltages"], elements_dict["poste"]
        )
        value_max_voltages = human_analysis.calc_diff_volt(
            contingencies_dict[key]["max_voltages"], elements_dict["poste"]
        )
        value_max_flows = human_analysis.calc_diff_max_flow(contingencies_dict[key]["max_flow"])
        value_constr_gen_Q = human_analysis.calc_constr_gen_Q(
            contingencies_dict[key]["constr_gen_Q"], elements_dict["groupe"]
        )
        value_constr_gen_U = human_analysis.calc_constr_gen_U(
            contingencies_dict[key]["constr_gen_U"], elements_dict["groupe"]
        )
        value_constr_volt = human_analysis.calc_constr_volt(
            contingencies_dict[key]["constr_volt"], elements_dict["noeud"]
        )
        value_constr_flow = human_analysis.calc_constr_flow(
            contingencies_dict[key]["constr_flow"], elements_dict["quadripole"]
        )
        value_n_iter = contingencies_dict[key]["n_iter"]
        value_affected_elem = len(contingencies_dict[key]["affected_elements"])
        value_constr_res_node = len(contingencies_dict[key]["res_node"])
        value_coef_report = len(contingencies_dict[key]["coef_report"])

        value_tap_changer = 0
        if tap_changers:
            for tap in contingencies_dict[key]["tap_changers"]:
                if int(tap["stopper"]) == 0:
                    value_tap_changer += abs(tap["diff_value"])
                else:
                    value_tap_changer += STD_TAP_VALUE

        contingencies_df["NUM"].append(key)
        contingencies_df["NAME"].append(contingencies_dict[key]["name"])
        contingencies_df["MIN_VOLT"].append(value_min_voltages)
        contingencies_df["MAX_VOLT"].append(value_max_voltages)
        contingencies_df["MAX_FLOW"].append(value_max_flows)
        contingencies_df["N_ITER"].append(value_n_iter)
        contingencies_df["AFFECTED_ELEM"].append(value_affected_elem)
        contingencies_df["CONSTR_GEN_Q"].append(value_constr_gen_Q)
        contingencies_df["CONSTR_GEN_U"].append(value_constr_gen_U)
        contingencies_df["CONSTR_VOLT"].append(value_constr_volt)
        contingencies_df["CONSTR_FLOW"].append(value_constr_flow)
        contingencies_df["RES_NODE"].append(value_constr_res_node)
        contingencies_df["COEF_REPORT"].append(value_coef_report)
        if tap_changers:
            contingencies_df["TAP_CHANGERS"].append(value_tap_changer)
        if predicted_score:
            contingencies_df["PREDICTED_SCORE"].append(contingencies_dict[key]["final_score"])

        if contingencies_dict[key]["status"] != 0:
            if contingencies_dict[key]["status"] == 1:
                error_contg[key] = "Divergence"
            elif contingencies_dict[key]["status"] == 2:
                error_contg[key] = "Generic fail"
            elif contingencies_dict[key]["status"] == 3:
                error_contg[key] = "No computation"
            elif contingencies_dict[key]["status"] == 4:
                error_contg[key] = "Interrupted"
            elif contingencies_dict[key]["status"] == 5:
                error_contg[key] = "No output"
            elif contingencies_dict[key]["status"] == 6:
                error_contg[key] = "Nonrealistic solution"
            elif contingencies_dict[key]["status"] == 7:
                error_contg[key] = "Power balance fail"
            elif contingencies_dict[key]["status"] == 8:
                error_contg[key] = "Timeout"
            else:
                error_contg[key] = "Final state unknown"

    return pd.DataFrame.from_dict(contingencies_df, orient="columns").set_index("NUM"), error_contg


def predict_scores(contingencies_df, model_filename):
    # Predict with the machine learning model

    model = pickle.load(open(model_filename, "rb"))
    contg_scores = {}

    for i in contingencies_df.index:
        contg_scores[str(i)] = model.predict(contingencies_df.loc[[i]].drop("NAME", axis=1))[0]

    return contg_scores


def analyze_loadflow_results(contingencies_dict, elements_dict, tap_changers):
    # Predict the difference between Hades and Dynamo load flow resolution using only Hades
    # resolution. For this, a previously trained model is used, which can be found in the same
    # folder as this script, and which varies depending on whether the tap changers are active or
    # not.

    contingencies_df, error_contg = convert_dict_to_df(
        contingencies_dict, elements_dict, tap_changers
    )

    model_path = Path(os.path.dirname(os.path.realpath(__file__)))

    if tap_changers:
        model_path = model_path / "ML_taps.pkl"
    else:
        model_path = model_path / "ML_no_taps.pkl"

    contg_scores = predict_scores(
        contingencies_df,
        model_path,
    )

    for key in contingencies_dict.keys():
        if key in error_contg:
            contingencies_dict[key]["final_score"] = error_contg[key]
        else:
            contingencies_dict[key]["final_score"] = contg_scores[key]

    return contingencies_dict


def argument_parser(command_list):
    # Define command line arguments

    p = argparse.ArgumentParser()

    if "df_path" in command_list:
        p.add_argument(
            "df_path",
            help="enter the path to the training dataframe",
        )

    if "df_target" in command_list:
        p.add_argument(
            "df_target",
            help="enter the path to the training dataframe",
        )

    if "model_path" in command_list:
        p.add_argument(
            "model_path",
            help="enter the path where to save the trained models",
        )

    args = p.parse_args()
    return args


def normalize_LR(X, coefs):
    # Get the median of all values to normalize the weights of LR and view the most important ones
    coefs_norm = []

    cols = list(X.columns)

    for i in range(len(cols)):
        coefs_norm.append(X[cols[i]].mean() * coefs[i])

    return coefs_norm


# FROM HERE:
# command line executables


def train_test_loadflow_results():
    # Function to train and test different machine learning models in order to compare them and
    # get the best one to include it in the package and make the predictions

    pd.options.mode.chained_assignment = None  # default='warn'
    args = argument_parser(["df_path", "model_path"])

    df_path = Path(args.df_path)
    model_path = Path(args.model_path)

    # Analyze the loadflow results through machine learning models
    contingencies_df = pd.read_csv(df_path, sep=";")

    # contingencies_df = contingencies_df.drop(["NUM"], axis=1)
    contingencies_df = contingencies_df.drop(["PREDICTED_SCORE"], axis=1)
    contingencies_df = contingencies_df.loc[contingencies_df["STATUS"] == "BOTH"]
    contingencies_df = contingencies_df.drop(["STATUS"], axis=1)
    contingencies_df = contingencies_df.dropna()

    contingencies_df = contingencies_df.sample(frac=1)

    y = contingencies_df.pop("REAL_SCORE")
    X = contingencies_df.drop("NAME", axis=1)

    # model_GBR = GradientBoostingRegressor(learning_rate=0.1104, n_estimators=700, max_depth=12)
    model_GBR = GradientBoostingRegressor(learning_rate=0.11, n_estimators=700, max_depth=12)
    model_LR = LinearRegression()

    cv = KFold(n_splits=5)

    n_scores_GBR = cross_val_score(
        model_GBR,
        X,
        y,
        scoring="neg_mean_absolute_error",
        cv=cv,
        n_jobs=-1,
        error_score="raise",
        verbose=3,
    )

    print("MAE GBR: %.3f (%.3f)" % (mean(n_scores_GBR), std(n_scores_GBR)))

    n_scores_LR = cross_val_score(
        model_LR,
        X,
        y,
        scoring="neg_mean_absolute_error",
        cv=cv,
        n_jobs=-1,
        error_score="raise",
        verbose=3,
    )

    print("MAE LR: %.3f (%.3f)" % (mean(n_scores_LR), std(n_scores_LR)))

    # fit the model on the whole dataset
    model_GBR = GradientBoostingRegressor(learning_rate=0.11, n_estimators=700, max_depth=12)
    model_GBR.fit(X, y)

    model_LR = LinearRegression()
    model_LR.fit(X, y)

    cols = list(X.columns)
    coefs = list(model_LR.coef_)
    print()
    print("LR weights")
    print("INTERCEPTION", model_LR.intercept_)
    for i in range(len(cols)):
        print(cols[i], coefs[i])

    print()
    print("LR weights normalized")
    print("INTERCEPTION", model_LR.intercept_)

    coefs_norm = normalize_LR(X, coefs)

    for i in range(len(cols)):
        print(cols[i], coefs_norm[i])

    pickle.dump(model_GBR, open(model_path / "GBR_model.pkl", "wb"))
    pickle.dump(model_LR, open(model_path / "LR_model.pkl", "wb"))

    print("Models saved")

    # Search for the best hyperparameters
    """
    from skopt import BayesSearchCV
    from skopt.space import Real, Integer
    np.int = np.int64
    parameters = {
        "learning_rate": Real(0.08, 0.4, prior="log-uniform"),
        "n_estimators": Integer(400, 800),
        "max_depth": Integer(4, 12),
    }
    model_GBR = GradientBoostingRegressor()

    clf = BayesSearchCV(
        estimator=model_GBR,
        search_spaces=parameters,
        scoring="neg_mean_absolute_error",
        cv=5,
        verbose=5,
        n_jobs=8,
        random_state=0,
        n_iter=50,
    )
    clf.fit(X, y)

    print(clf.cv_results_)
    pd.DataFrame.from_dict(clf.cv_results_, orient="columns").to_csv(
        model_path / "BayesSearchCV.csv", index=False
    )
    """
