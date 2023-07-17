STD_TAP_VALUE = 20


def calc_diff_volt(contingency_values, loadflow_values):
    sum_diffs = len(contingency_values)

    for poste_v in contingency_values:
        sum_diffs += abs(poste_v[1] - loadflow_values[poste_v[0]]["volt"])

    return sum_diffs


def calc_diff_max_flow(list_values):
    # TODO: Check with JL the concept of max flow and if the calc is okay
    sum_diffs = len(list_values)

    for max_flow in list_values:
        sum_diffs += abs(max_flow[1] / 10)

    return sum_diffs


def calc_constr_gen_Q(contingency_values, elem_dict):
    # TODO: Check if it is okay for JL

    score_constr = len(contingency_values)
    for constr in contingency_values:
        score_constr += abs(float(constr["after"]) - float(constr["before"])) * (
            1 + elem_dict[constr["elem_num"]]["volt_level"] / 10
        )

    return score_constr


def calc_constr_gen_U(contingency_values, elem_dict):
    # TODO: Check if it is okay for JL
    score_constr = len(contingency_values)
    for constr in contingency_values:
        score_constr += abs(float(constr["after"]) - float(constr["before"])) * (
            1 + elem_dict[constr["elem_num"]]["volt_level"] / 10
        )

    return score_constr


def calc_constr_volt(contingency_values, elem_dict):
    # TODO: Check if it is okay for JL
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
    # TODO: Check if it is okay for JL
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

    """
    final_value = 0
    for volt_constr in contingency_values:
        tempo = int(volt_constr["tempo"])
        if tempo == 99999 or tempo == 9999:
            final_value += 10
        else:
            tempo = tempo / 100
            final_value += (1 / (tempo * tempo)) * 10000

    """

    return final_value


def analyze_loadflow_results_continuous(contingencies_dict, elements_dict):
    # TODO: Explain what should be done
    # TODO: Implement it

    w_volt_min = 0.48453439427510003
    w_volt_max = -0.054528360371039364
    w_iter = 58.49003508266973
    w_poste = 11.40520295890738
    w_constr_gen_Q = 6.5659622388617755
    w_constr_gen_U = 6.963318810448982e-13
    w_constr_volt = -2.2173873238553075
    w_constr_flow = 17.40705542826712
    w_node = 554.1470097201553
    w_tap = 1.1482761323898152
    w_flow = 0.6367911705557392
    w_coefreport = 0.2262723051576275
    independent_term = 3919.8977272417924

    # dict_keys(['coef_report'])

    # TODO: Investigate if the 'calc_duration' can be interesting

    # TODO: Finished here, it remains to apply the new value of voltage level from the dictionary of elements dict to the calculations of the constraints

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
                    match int(tap["stopper"]):
                        case 0:
                            total_tap_value += abs(tap["diff_value"]) * w_tap
                        case 1 | 2 | 3:
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
            match contingencies_dict[key]["status"]:
                case 1:
                    contingencies_dict[key]["final_score"] = "Divergence"
                case 2:
                    contingencies_dict[key]["final_score"] = "Generic fail"
                case 3:
                    contingencies_dict[key]["final_score"] = "No computation"
                case 4:
                    contingencies_dict[key]["final_score"] = "Interrupted"
                case 5:
                    contingencies_dict[key]["final_score"] = "No output"
                case 6:
                    contingencies_dict[key]["final_score"] = "Nonrealistic solution"
                case 7:
                    contingencies_dict[key]["final_score"] = "Power balance fail"
                case 8:
                    contingencies_dict[key]["final_score"] = "Timeout"
                case _:
                    contingencies_dict[key]["final_score"] = "Final state unknown"

    return contingencies_dict
