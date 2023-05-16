import os
import argparse
from pathlib import Path
from lxml import etree
import pandas as pd
import pickle
from numpy import mean, std
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RepeatedKFold
from dynawo_contingencies_screening.analyze_loadflow import human_analysis


def convert_dict_to_df(contingencies_dict, elements_dict, disc_cont, score_target=False):
    contingencies_df = {
        "NUM": [],
        "NAME": [],
        "MIN_VOLT": [],
        "MAX_VOLT": [],
        "N_ITER": [],
        "AFFECTED_ELEM": [],
        "CONSTR_GEN_Q": [],
        "CONSTR_GEN_U": [],
        "CONSTR_VOLT": [],
        "CONSTR_FLOW": [],
    }

    if score_target:
        contingencies_df["SCORE_TARGET"] = []

    error_contg = {}
    # If we want continuous data or discrete
    if disc_cont:
        # Discrete
        for key in contingencies_dict.keys():
            if contingencies_dict[key]["status"] == 0:
                value_min_voltages = len(contingencies_dict[key]["min_voltages"])
                value_max_voltages = len(contingencies_dict[key]["max_voltages"])
                value_constr_gen_Q = len(contingencies_dict[key]["constr_gen_Q"])
                value_constr_gen_U = len(contingencies_dict[key]["constr_gen_U"])
                value_constr_volt = len(contingencies_dict[key]["constr_volt"])
                value_constr_flow = len(contingencies_dict[key]["constr_flow"])
                value_n_iter = contingencies_dict[key]["n_iter"]
                value_affected_elem = len(contingencies_dict[key]["affected_elements"])

                contingencies_df["NUM"].append(key)
                contingencies_df["NAME"].append(contingencies_dict[key]["name"])
                contingencies_df["MIN_VOLT"].append(value_min_voltages)
                contingencies_df["MAX_VOLT"].append(value_max_voltages)
                contingencies_df["N_ITER"].append(value_n_iter)
                contingencies_df["AFFECTED_ELEM"].append(value_affected_elem)
                contingencies_df["CONSTR_GEN_Q"].append(value_constr_gen_Q)
                contingencies_df["CONSTR_GEN_U"].append(value_constr_gen_U)
                contingencies_df["CONSTR_VOLT"].append(value_constr_volt)
                contingencies_df["CONSTR_FLOW"].append(value_constr_flow)
                if score_target:
                    contingencies_df["SCORE_TARGET"].append(contingencies_dict[key]["final_score"])
            else:
                match contingencies_dict[key]["status"]:
                    case 1:
                        error_contg[key] = "Divergence"
                    case 2:
                        error_contg[key] = "Generic fail"
                    case 3:
                        error_contg[key] = "No computation"
                    case 4:
                        error_contg[key] = "Interrupted"
                    case 5:
                        error_contg[key] = "No output"
                    case 6:
                        error_contg[key] = "Nonrealistic solution"
                    case 7:
                        error_contg[key] = "Power balance fail"
                    case 8:
                        error_contg[key] = "Timeout"
                    case _:
                        error_contg[key] = "Final state unknown"
    else:
        # Continuous
        for key in contingencies_dict.keys():
            if contingencies_dict[key]["status"] == 0:

                value_min_voltages = human_analysis.calc_diff_volt(
                    contingencies_dict[key]["min_voltages"], elements_dict["poste"]
                )
                value_max_voltages = human_analysis.calc_diff_volt(
                    contingencies_dict[key]["max_voltages"], elements_dict["poste"]
                )
                value_constr_gen_Q = human_analysis.calc_constr_gen_Q(
                    contingencies_dict[key]["constr_gen_Q"]
                )
                value_constr_gen_U = human_analysis.calc_constr_gen_U(
                    contingencies_dict[key]["constr_gen_U"]
                )
                value_constr_volt = human_analysis.calc_constr_volt(
                    contingencies_dict[key]["constr_volt"]
                )
                value_constr_flow = human_analysis.calc_constr_flow(
                    contingencies_dict[key]["constr_flow"]
                )
                value_n_iter = contingencies_dict[key]["n_iter"]
                value_affected_elem = len(contingencies_dict[key]["affected_elements"])

                contingencies_df["NUM"].append(key)
                contingencies_df["NAME"].append(contingencies_dict[key]["name"])
                contingencies_df["MIN_VOLT"].append(value_min_voltages)
                contingencies_df["MAX_VOLT"].append(value_max_voltages)
                contingencies_df["N_ITER"].append(value_n_iter)
                contingencies_df["AFFECTED_ELEM"].append(value_affected_elem)
                contingencies_df["CONSTR_GEN_Q"].append(value_constr_gen_Q)
                contingencies_df["CONSTR_GEN_U"].append(value_constr_gen_U)
                contingencies_df["CONSTR_VOLT"].append(value_constr_volt)
                contingencies_df["CONSTR_FLOW"].append(value_constr_flow)
                if score_target:
                    contingencies_df["SCORE_TARGET"].append(contingencies_dict[key]["final_score"])
            else:
                match contingencies_dict[key]["status"]:
                    case 1:
                        error_contg[key] = "Divergence"
                    case 2:
                        error_contg[key] = "Generic fail"
                    case 3:
                        error_contg[key] = "No computation"
                    case 4:
                        error_contg[key] = "Interrupted"
                    case 5:
                        error_contg[key] = "No output"
                    case 6:
                        error_contg[key] = "Nonrealistic solution"
                    case 7:
                        error_contg[key] = "Power balance fail"
                    case 8:
                        error_contg[key] = "Timeout"
                    case _:
                        error_contg[key] = "Final state unknown"

    return pd.DataFrame.from_dict(contingencies_df, orient="columns").set_index("NUM"), error_contg


def predict_scores(contingencies_df, model_filename):
    model = pickle.load(open(model_filename, "rb"))
    contg_scores = {}

    for i in contingencies_df.index:
        contg_scores[str(i)] = model.predict(contingencies_df.loc[[i]].drop("NAME", axis=1))[0]

    return contg_scores


def analyze_loadflow_results(contingencies_dict, elements_dict, disc_cont, tap_changers):
    # Analyze the loadflow results through machine learning models

    contingencies_df, error_contg = convert_dict_to_df(
        contingencies_dict, elements_dict, disc_cont
    )

    model_path = Path(os.path.dirname(os.path.realpath(__file__)))

    if disc_cont and tap_changers:
        model_path = model_path / "ML_disc_taps.pkl"
    elif disc_cont and not tap_changers:
        model_path = model_path / "ML_disc_no_taps.pkl"
    elif not disc_cont and tap_changers:
        model_path = model_path / "ML_cont_taps.pkl"
    else:
        model_path = model_path / "ML_cont_no_taps.pkl"

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

    if "model_path" in command_list:
        p.add_argument(
            "model_path",
            help="enter the path where to save the trained models",
        )

    args = p.parse_args()
    return args


def train_test_loadflow_results():

    args = argument_parser(["df_path", "model_path"])

    df_path = Path(args.df_path)
    model_path = Path(args.model_path)

    # Analyze the loadflow results through machine learning models
    contingencies_df = pd.read_csv(df_path, sep=";", index_col="NUM")

    y = contingencies_df.pop("SCORE_TARGET")
    X = contingencies_df.drop("NAME", axis=1)

    model_GBR = GradientBoostingRegressor()
    model_RF = RandomForestRegressor(max_depth=3, random_state=0)

    cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=0)

    n_scores_GBR = cross_val_score(
        model_GBR, X, y, scoring="neg_mean_absolute_error", cv=cv, n_jobs=-1, error_score="raise"
    )
    n_scores_RF = cross_val_score(
        model_RF, X, y, scoring="neg_mean_absolute_error", cv=cv, n_jobs=-1, error_score="raise"
    )

    print("MAE GBR: %.3f (%.3f)" % (mean(n_scores_GBR), std(n_scores_GBR)))

    print("MAE RF: %.3f (%.3f)" % (mean(n_scores_RF), std(n_scores_RF)))

    # fit the model on the whole dataset
    model_GBR = GradientBoostingRegressor()
    model_GBR.fit(X, y)

    model_RF = RandomForestRegressor(max_depth=3, random_state=0)
    model_RF.fit(X, y)

    pickle.dump(model_GBR, open(model_path / "GBR_model.pkl", "wb"))
    pickle.dump(model_RF, open(model_path / "RF_model.pkl", "wb"))

    print("Models saved")
