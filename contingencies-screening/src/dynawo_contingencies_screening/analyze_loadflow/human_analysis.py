STD_TAP_VALUE = 20


def analyze_loadflow_results_discrete(contingencies_dict, elements_dict):
    # TODO: Explain what should be done

    w_volt = 1
    w_iter = 10
    w_poste = 10
    w_constr_gen_Q = 10
    w_constr_gen_U = 10
    w_constr_volt = 10
    w_constr_flow = 10
    w_node = 10
    w_tap = 10

    for key in contingencies_dict.keys():
        if contingencies_dict[key]["status"] == 0:
            contingencies_dict[key]["final_score"] = round(
                (
                    (
                        len(contingencies_dict[key]["min_voltages"])
                        + len(contingencies_dict[key]["max_voltages"])
                    )
                    * w_volt
                    + contingencies_dict[key]["n_iter"] * w_iter
                    + len(contingencies_dict[key]["affected_elements"]) * w_poste
                    + len(contingencies_dict[key]["constr_gen_Q"]) * w_constr_gen_Q
                    + len(contingencies_dict[key]["constr_gen_U"]) * w_constr_gen_U
                    + len(contingencies_dict[key]["constr_volt"]) * w_constr_volt
                    + len(contingencies_dict[key]["constr_flow"]) * w_constr_flow
                    + len(contingencies_dict[key]["res_node"]) * w_node
                ),
                4,
            )
            if "tap_changers" in contingencies_dict[key].keys():
                total_tap_value = 0
                for tap in contingencies_dict[key]["tap_changers"]:
                    match tap["stopper"]:
                        case "0":
                            total_tap_value += abs(int(tap["diff_value"])) * w_tap
                        case "1" | "2" | "3":
                            total_tap_value += STD_TAP_VALUE * w_tap
                contingencies_dict[key]["final_score"] += total_tap_value
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


def calc_diff_volt(contingency_values, loadflow_values):
    sum_diffs = 0

    for poste_v in contingency_values:
        sum_diffs += abs(poste_v[1] - loadflow_values[poste_v[0]]["volt"])

    return sum_diffs


def calc_constr_gen_Q(contingency_values):
    constr_gen_Q_score = 0
    w_reactive_level = 0.1
    base_value = 0.5

    for entry in contingency_values:
        constr_gen_Q_score += int(entry["type"]) * w_reactive_level + base_value

    return round(constr_gen_Q_score, 1)


def calc_constr_gen_U(contingency_values):
    constr_gen_U_score = 0
    w_voltage_level = 0.1
    base_value = 0.5

    for entry in contingency_values:
        constr_gen_U_score += int(entry["type"]) * w_voltage_level + base_value

    return round(constr_gen_U_score, 1)


def calc_constr_volt(contingency_values):
    final_value = 0
    w_thresh_value = 0.5

    for volt_constr in contingency_values:
        exceeding_volt = round(float(volt_constr["after"]) - float(volt_constr["limit"]), 0)
        final_value += exceeding_volt * (int(volt_constr["threshType"]) * w_thresh_value)
        tempo = int(volt_constr["tempo"])
        if tempo == 99999:
            final_value += 5
        else:
            final_value += (1 / (tempo * tempo)) * 1000

    return final_value


def calc_constr_flow(contingency_values):
    final_value = 0
    w_thresh_value = 0.5

    for flow_constr in contingency_values:
        exceeding_flow = round(float(flow_constr["after"]) - float(flow_constr["limit"]), 0)
        final_value += exceeding_flow * w_thresh_value
        tempo = int(flow_constr["tempo"])
        if tempo == 9999:
            final_value += 10
        else:
            tempo = tempo / 100
            final_value += (1 / (tempo * tempo)) * 10000

    return final_value


def calc_affected_elements(contingency_values, elements_dict):
    final_value = 0
    w_voltage_level = 0.1

    for entry in contingency_values:
        poste_num = int(entry["poste"])
        poste_voltage_level = int(elements_dict["poste"][poste_num]["nivTension"])
        final_value += poste_voltage_level * w_voltage_level * len(entry["elements_list"])

    return final_value


def analyze_loadflow_results_continuous(contingencies_dict, elements_dict):
    # TODO: Explain what should be done
    # TODO: Implement it
    w_volt = 10
    w_iter = 10
    w_poste = 10
    w_constr_gen_Q = 10
    w_constr_gen_U = 10
    w_constr_volt = 10
    w_constr_flow = 10
    w_node = 10
    w_tap = 10

    for key in contingencies_dict.keys():
        if contingencies_dict[key]["status"] == 0:
            diff_min_voltages = calc_diff_volt(
                contingencies_dict[key]["min_voltages"], elements_dict["poste"]
            )
            diff_max_voltages = calc_diff_volt(
                contingencies_dict[key]["max_voltages"], elements_dict["poste"]
            )

            value_constr_gen_Q = calc_constr_gen_Q(contingencies_dict[key]["constr_gen_Q"])
            value_constr_gen_U = calc_constr_gen_U(contingencies_dict[key]["constr_gen_U"])
            value_constr_volt = calc_constr_volt(contingencies_dict[key]["constr_volt"])
            value_constr_flow = calc_constr_flow(contingencies_dict[key]["constr_flow"])
            value_affected_elements = calc_affected_elements(
                contingencies_dict[key]["affected_elements"], elements_dict
            )

            contingencies_dict[key]["final_score"] = round(
                (
                    (diff_min_voltages + diff_max_voltages) * w_volt
                    + contingencies_dict[key]["n_iter"] * w_iter
                    + value_affected_elements * w_poste
                    + value_constr_gen_Q * w_constr_gen_Q
                    + value_constr_gen_U * w_constr_gen_U
                    + value_constr_volt * w_constr_volt
                    + value_constr_flow * w_constr_flow
                    + len(contingencies_dict[key]["res_node"]) * w_node
                ),
                4,
            )
            if "tap_changers" in contingencies_dict[key].keys():
                total_tap_value = 0
                for tap in contingencies_dict[key]["tap_changers"]:
                    match tap["stopper"]:
                        case "0":
                            total_tap_value += abs(int(tap["diff_value"])) * w_tap
                        case "1" | "2" | "3":
                            total_tap_value += STD_TAP_VALUE * w_tap
                contingencies_dict[key]["final_score"] += total_tap_value
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
