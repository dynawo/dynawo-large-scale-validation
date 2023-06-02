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


def calc_matching_volt_constr(matched_volt_constr):
    diff_marching_volt = 0

    for case_diffs_list in matched_volt_constr.values():
        for case_diffs in case_diffs_list:
            print(case_diffs)
        print()

    return diff_marching_volt


def calc_matching_flow_constr(matched_flow_constr):
    diff_marching_flow = 0

    for case_diffs_list in matched_flow_constr.values():
        for case_diffs in case_diffs_list:
            print(case_diffs)
        print()

    return diff_marching_flow


def calc_matching_gen_Q_constr(matched_gen_Q_constr):
    diff_marching_gen_Q = 0
    # TODO: Implement it
    return diff_marching_gen_Q


def calc_matching_gen_U_constr(matched_gen_U_constr):
    diff_marching_gen_U = 0
    # TODO: Implement it
    return diff_marching_gen_U


def match_constraints(hades_constr, dwo_constraints):
    matched_constr = {}

    for constr_hds in hades_constr:
        for constr_dwo in dwo_constraints:
            if constr_hds["elem_name"] == constr_dwo["modelName"]:
                if constr_hds["elem_name"] in matched_constr:
                    matched_constr[constr_hds["elem_name"]].append([constr_hds, constr_dwo])
                else:
                    matched_constr[constr_hds["elem_name"]] = [[constr_hds, constr_dwo]]

    return matched_constr


def get_unmatched_constr(hades_constr, dwo_constraints, matched_constr):

    unique_constr_hds = []
    unique_constr_dwo = []

    for constr_hds in hades_constr:
        if constr_hds["elem_name"] not in matched_constr:
            unique_constr_hds.append(constr_hds)

    for constr_dwo in dwo_constraints:
        if constr_dwo["elem_name"] not in matched_constr:
            unique_constr_dwo.append(constr_dwo)

    return unique_constr_hds, unique_constr_dwo


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
    matched_volt_constr = match_constraints(hades_constr_volt, dwo_volt_constraints)
    matched_flow_constr = match_constraints(hades_constr_flow, dwo_flow_constraints)
    matched_gen_Q_constr = match_constraints(hades_constr_gen_Q, dwo_gen_Q_constraints)
    matched_gen_U_constr = match_constraints(hades_constr_gen_U, dwo_gen_U_constraints)

    unique_constr_volt_hds, unique_constr_volt_dwo = get_unmatched_constr(
        hades_constr_volt, dwo_volt_constraints, matched_volt_constr
    )
    unique_constr_flow_hds, unique_constr_flow_dwo = get_unmatched_constr(
        hades_constr_flow, dwo_flow_constraints, matched_flow_constr
    )
    unique_constr_gen_Q_hds, unique_constr_gen_Q_dwo = get_unmatched_constr(
        hades_constr_gen_Q, dwo_gen_Q_constraints, matched_gen_Q_constr
    )
    unique_constr_gen_U_hds, unique_constr_gen_U_dwo = get_unmatched_constr(
        hades_constr_gen_U, dwo_gen_U_constraints, matched_gen_U_constr
    )

    diff_marching_volt = calc_matching_volt_constr(matched_volt_constr)
    diff_marching_flow = calc_matching_flow_constr(matched_flow_constr)
    diff_marching_gen_Q = calc_matching_gen_Q_constr(matched_gen_Q_constr)
    diff_marching_gen_U = calc_matching_gen_U_constr(matched_gen_U_constr)

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
