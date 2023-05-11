from lxml import etree


def analyze_loadflow_results_discrete(contingencies_dict):
    # TODO: Explain what should be done

    w_volt = 1
    w_iter = 10
    w_poste = 10
    w_constrait = 10

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
                    + (
                        len(contingencies_dict[key]["constr_gen_Q"])
                        + len(contingencies_dict[key]["constr_gen_U"])
                        + len(contingencies_dict[key]["constr_volt"])
                        + len(contingencies_dict[key]["constr_flow"])
                    )
                    * w_constrait
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


def analyze_loadflow_results_continuous(contingencies_dict):
    # TODO: Explain what should be done
    # TODO: Implement it
    w_volt = 1
    w_iter = 10
    w_poste = 10
    w_constrait = 10

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
                    + (
                        len(contingencies_dict[key]["constr_gen_Q"])
                        + len(contingencies_dict[key]["constr_gen_U"])
                        + len(contingencies_dict[key]["constr_volt"])
                        + len(contingencies_dict[key]["constr_flow"])
                    )
                    * w_constrait
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
