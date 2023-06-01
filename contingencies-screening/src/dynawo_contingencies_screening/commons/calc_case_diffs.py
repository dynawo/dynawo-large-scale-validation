def get_hades_id(case, sorted_loadflow_score_list):
    for i in range(len(sorted_loadflow_score_list)):
        if case == sorted_loadflow_score_list[i][1]["name"]:
            return i
    exit("Error, hades index not found")


def compare_status(hades_status, dynawo_status):
    print(hades_status)
    print(dynawo_status)
    if hades_status == 0 and dynawo_status == "CONVERGENCE":
        return "BOTH"
    elif hades_status != 0 and dynawo_status == "CONVERGENCE":
        return "DWO"
    elif hades_status == 0 and dynawo_status == "DIVERGENCE":
        return "HDS"
    else:
        return "NONE"


def compare_taps(hades_taps, dwo_taps):
    print(hades_taps)
    print(dwo_taps)
    return 1000


def compare_constraints(
    hades_constr_volt, hades_constr_flow, hades_constr_gen_Q, hades_constr_gen_U, dwo_constraints
):
    # Separe dynawo constraints
    dwo_volt_constraints = []
    dwo_gen_Q_constraints = []
    dwo_gen_U_constraints = []
    dwo_flow_constraints = []
    dwo_non_defined_constraints = []

    for constraint in dwo_constraints:
        if constraint["type"] == "Node":
            dwo_volt_constraints.append(constraint)
        elif constraint["type"] == "Line":
            dwo_flow_constraints.append(constraint)
        # TODO: Change this condition
        elif constraint["type"] == "Pending":
            dwo_gen_Q_constraints.append(constraint)
        # TODO: Change this condition
        elif constraint["type"] == "Pending":
            dwo_gen_U_constraints.append(constraint)
        else:
            dwo_non_defined_constraints.append(constraint)

    # Compare volt constraints
    matched_volt_constr = []

    for volt_constr_hds in hades_constr_volt:
        for volt_constr_dwo in dwo_volt_constraints:
            if volt_constr_hds["elem_name"] == volt_constr_dwo["modelName"]:
                matched_volt_constr.append([volt_constr_hds, volt_constr_dwo])

    print(matched_volt_constr)

    return 1000


def calculate_diffs_hades_dynawo(hades_info, dwo_info):

    dict_diffs = {}
    # Compare status status
    status_diff = compare_status(hades_info[1]["status"], dwo_info["status"])

    if status_diff == "DWO" or status_diff == "HDS":
        dict_diffs["conv_status"] = status_diff
        dict_diffs["diff_value"] = 100000
    elif status_diff == "NONE":
        dict_diffs["conv_status"] = status_diff
        dict_diffs["diff_value"] = 50000
    else:
        dict_diffs["conv_status"] = status_diff

        # Get tap diffs
        if "tap_changers" in hades_info[1]:
            taps_diff = compare_taps(hades_info[1]["tap_changers"], dwo_info["tap_changers"])

        # Get constraint diffs
        constraints_diffs = compare_constraints(
            hades_info[1]["constr_volt"],
            hades_info[1]["constr_flow"],
            hades_info[1]["constr_gen_Q"],
            hades_info[1]["constr_gen_U"],
            dwo_info["constraints"],
        )

    return dict_diffs
