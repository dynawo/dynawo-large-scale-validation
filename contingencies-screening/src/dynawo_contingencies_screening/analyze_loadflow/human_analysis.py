import json
import os
from pathlib import Path


def calc_diff_volt(contingency_values, loadflow_values):
    # Calculate the value of the metric to be able to predict if there will be a difference
    # between Hades and Dynawo

    sum_diffs = len(contingency_values)

    for poste_v in contingency_values:
        sum_diffs += abs(poste_v[1] - loadflow_values[poste_v[0]]["volt"])

    return sum_diffs


def calc_diff_max_flow(list_values):
    # Calculate the value of the metric to be able to predict if there will be a difference
    # between Hades and Dynawo

    sum_diffs = len(list_values)

    for max_flow in list_values:
        sum_diffs += abs(max_flow[1] / 10)

    return sum_diffs


def calc_constr_gen_Q(contingency_values, elem_dict):
    # Calculate the value of the metric to be able to predict if there will be a difference
    # between Hades and Dynawo

    score_constr = len(contingency_values)
    for constr in contingency_values:
        score_constr += abs(float(constr["after"]) - float(constr["before"])) * (
            1 + elem_dict[constr["elem_num"]]["volt_level"] / 10
        )

    return score_constr


def calc_constr_gen_U(contingency_values, elem_dict):
    # Calculate the value of the metric to be able to predict if there will be a difference
    # between Hades and Dynawo

    score_constr = len(contingency_values)
    for constr in contingency_values:
        score_constr += abs(float(constr["after"]) - float(constr["before"])) * (
            1 + elem_dict[constr["elem_num"]]["volt_level"] / 10
        )

    return score_constr


def calc_constr_volt(contingency_values, elem_dict):
    # Calculate the value of the metric to be able to predict if there will be a difference
    # between Hades and Dynawo

    final_value = 0

    for volt_constr in contingency_values:
        tempo = int(volt_constr["tempo"])
        if tempo == 99999 or tempo == 9999:
            final_value += 5
        else:
            value = (1 / tempo) * 10000

            if value > 100:
                value = 100

            final_value += value * (1 + elem_dict[volt_constr["elem_num"]]["volt_level"] / 10)

    return final_value


def calc_constr_flow(contingency_values, elem_dict):
    # Calculate the value of the metric to be able to predict if there will be a difference
    # between Hades and Dynawo

    final_value = 0

    for flow_constr in contingency_values:
        tempo = int(flow_constr["tempo"])
        if tempo == 99999 or tempo == 9999:
            final_value += 5
        else:
            value = (1 / tempo) * 10000

            if value > 100:
                value = 100

            final_value += value * (1 + elem_dict[flow_constr["elem_num"]]["volt_level"] / 10)

    return final_value


STD_TAP_VALUE = 20


def analyze_loadflow_results_continuous(
    contingencies_dict, elements_dict, tap_changers, model_path
):
    # Predict the difference between Hades and Dynawo's loadflow resolution using only Hades'
    # resolution. Each of the attributes has an assigned weight that shows its importance over
    # the final value.

    print(
        "\nWARNING: Remember that if you have selected the human analysis option, you must provide the path of a LR in JSON format that matches (has been trained) the option selected on the taps (activated or not activated).\n"
    )

    if model_path is None:
        model_path = Path(os.path.dirname(os.path.realpath(__file__)))
        if tap_changers:
            model_path = model_path / "LR_taps.json"
        else:
            model_path = model_path / "LR_no_taps.json"

    f = open(model_path)
    data = json.load(f)

    w_volt_min = data["MIN_VOLT"]
    w_volt_max = data["MAX_VOLT"]
    w_iter = data["N_ITER"]
    w_poste = data["AFFECTED_ELEM"]
    w_constr_gen_Q = data["CONSTR_GEN_Q"]
    w_constr_gen_U = data["CONSTR_GEN_U"]
    w_constr_volt = data["CONSTR_VOLT"]
    w_constr_flow = data["CONSTR_FLOW"]
    w_node = data["RES_NODE"]
    if tap_changers:
        w_tap = data["TAP_CHANGERS"]
    else:
        w_tap = 0
    w_flow = data["MAX_FLOW"]
    w_coefreport = data["COEF_REPORT"]
    independent_term = data["INTERCEPTION"]

    for key in contingencies_dict.keys():
        if contingencies_dict[key]["status"] == 0:
            diff_min_voltages = calc_diff_volt(
                contingencies_dict[key]["min_voltages"], elements_dict["poste"]
            )
            diff_max_voltages = calc_diff_volt(
                contingencies_dict[key]["max_voltages"], elements_dict["poste"]
            )

            diff_max_flows = calc_diff_max_flow(contingencies_dict[key]["max_flow"])

            value_constr_gen_Q = calc_constr_gen_Q(
                contingencies_dict[key]["constr_gen_Q"], elements_dict["groupe"]
            )
            value_constr_gen_U = calc_constr_gen_U(
                contingencies_dict[key]["constr_gen_U"], elements_dict["groupe"]
            )
            value_constr_volt = calc_constr_volt(
                contingencies_dict[key]["constr_volt"], elements_dict["noeud"]
            )
            value_constr_flow = calc_constr_flow(
                contingencies_dict[key]["constr_flow"], elements_dict["quadripole"]
            )

            total_tap_value = 0
            if "tap_changers" in contingencies_dict[key].keys():
                for tap in contingencies_dict[key]["tap_changers"]:
                    if int(tap["stopper"]) == 0:
                        total_tap_value += abs(tap["diff_value"]) * w_tap
                    else:
                        total_tap_value += STD_TAP_VALUE * w_tap

            contingencies_dict[key]["final_score"] = round(
                (
                    (diff_min_voltages * w_volt_min + diff_max_voltages * w_volt_max)
                    + contingencies_dict[key]["n_iter"] * w_iter
                    + len(contingencies_dict[key]["affected_elements"]) * w_poste
                    + value_constr_gen_Q * w_constr_gen_Q
                    + value_constr_gen_U * w_constr_gen_U
                    + value_constr_volt * w_constr_volt
                    + value_constr_flow * w_constr_flow
                    + len(contingencies_dict[key]["res_node"]) * w_node
                    + diff_max_flows * w_flow
                    + len(contingencies_dict[key]["coef_report"]) * w_coefreport
                    + total_tap_value
                    + independent_term
                ),
                4,
            )
        else:
            if contingencies_dict[key]["status"] == 1:
                contingencies_dict[key]["final_score"] = "Divergence"
            elif contingencies_dict[key]["status"] == 2:
                contingencies_dict[key]["final_score"] = "Generic fail"
            elif contingencies_dict[key]["status"] == 3:
                contingencies_dict[key]["final_score"] = "No computation"
            elif contingencies_dict[key]["status"] == 4:
                contingencies_dict[key]["final_score"] = "Interrupted"
            elif contingencies_dict[key]["status"] == 5:
                contingencies_dict[key]["final_score"] = "No output"
            elif contingencies_dict[key]["status"] == 6:
                contingencies_dict[key]["final_score"] = "Nonrealistic solution"
            elif contingencies_dict[key]["status"] == 7:
                contingencies_dict[key]["final_score"] = "Power balance fail"
            elif contingencies_dict[key]["status"] == 8:
                contingencies_dict[key]["final_score"] = "Timeout"
            else:
                contingencies_dict[key]["final_score"] = "Final state unknown"

    return contingencies_dict
