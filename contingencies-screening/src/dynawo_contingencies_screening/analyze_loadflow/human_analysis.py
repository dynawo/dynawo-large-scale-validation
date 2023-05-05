from lxml import etree


def analyze_loadflow_resuts(contingencies_dict, parsed_hades_output_file):
    # TODO: Explain what should be done
    # TODO: Implement it

    root = parsed_hades_output_file.getroot()
    ns = etree.QName(root).namespace

    coef_volt = 1
    coef_iter = 10
    coef_poste = 10
    coef_constrait = 10

    for key in contingencies_dict.keys():
        if contingencies_dict[key]["status"] == 0:
            contingencies_dict[key]["final_score"] = round(
                (
                    (
                        len(contingencies_dict[key]["min_voltages"])
                        + len(contingencies_dict[key]["max_voltages"])
                    )
                    * coef_volt
                    + contingencies_dict[key]["n_iter"] * coef_iter
                    + len(contingencies_dict[key]["affected_elements"]) * coef_poste
                    + (
                        len(contingencies_dict[key]["constr_gen_Q"])
                        + len(contingencies_dict[key]["constr_gen_U"])
                        + len(contingencies_dict[key]["constr_volt"])
                        + len(contingencies_dict[key]["constr_flow"])
                    )
                    * coef_constrait
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
