def get_hades_id(case, sorted_loadflow_score_list):
    for i in range(len(sorted_loadflow_score_list)):
        if case == sorted_loadflow_score_list[i][1]["name"]:
            return i
    exit("Error, hades index not found")


def compare_status(hades_status, dynawo_status):
    if hades_status == 0 and dynawo_status == "CONVERGENCE":
        return "BOTH"
    elif hades_status != 0 and dynawo_status == "CONVERGENCE":
        return "DWO"
    elif hades_status == 0 and dynawo_status == "DIVERGENCE":
        return "HDS"
    else:
        return "NONE"


def match_3_dictionaries(keys1, keys2, keys3):
    # Keys that match in all three dictionaries
    matching_keys2 = keys1.intersection(keys2)
    matching_keys3 = keys1.intersection(keys3)

    matching_keys = matching_keys2.union(matching_keys3)

    # Keys that don't match in each dictionary
    keys1_not_matching = keys1.difference(matching_keys)
    keys2_not_matching = keys2.difference(matching_keys)
    keys3_not_matching = keys3.difference(matching_keys)

    return matching_keys, keys1_not_matching, keys2_not_matching, keys3_not_matching


def compare_taps(hades_taps, dwo_taps):
    taps_diffs_dict = {}

    set_phase_taps = set(dwo_taps["phase_taps"].keys())
    set_ratio_taps = set(dwo_taps["ratio_taps"].keys())
    (
        matching_keys,
        keys_hades_not_matching,
        keys_phase_not_matching,
        keys_ratio_not_matching,
    ) = match_3_dictionaries(
        set([hds_tap["quadripole_name"] for hds_tap in hades_taps]),
        set_phase_taps,
        set_ratio_taps,
    )

    for hds_tap in hades_taps:
        tap_name = hds_tap["quadripole_name"]
        tap_diff_entry = {}
        '''
        if tap_name in matching_keys:
            if tap_name in set_ratio_taps:

                print(tap_name)
                print("hades_diff")
                print(int(hds_tap["previous_value"]) - int(hds_tap["after_value"]))
                print("dwo_diff")
                print(int(dwo_taps["ratio_taps"][tap_name]["tapPosition"]))
                print()
                print()
                """
                
                prev_value_diff = int(hds_tap["previous_value"]) - int(
                    dwo_taps["ratio_taps"][tap_name]["lowTapPosition"]
                )
                after_value_diff = int(hds_tap["after_value"]) - int(
                    dwo_taps["ratio_taps"][tap_name]["tapPosition"]
                )
                
                tap_diff_entry["tap_score"] = get_tap_score(ap_diff_entry["stopper"])
                tap_diff_entry["hds_prev"] = 
                tap_diff_entry["hds_post"] = 
                tap_diff_entry["dwo_prev"] = 
                tap_diff_entry["hds_post"] = 

                print("Hades prev")
                print(hds_tap["previous_value"])
                print("Dwo prev")
                print(dwo_taps["ratio_taps"][tap_name]["lowTapPosition"])
                print("Hades after")
                print(hds_tap["after_value"])
                print("Dwo after")
                print(dwo_taps["ratio_taps"][tap_name]["tapPosition"])
                print()
                print()
                """
            else:
                print(tap_name)
                print("hades_diff")
                print(int(hds_tap["previous_value"]) - int(hds_tap["after_value"]))
                print("dwo_diff_ph")
                print(int(dwo_taps["phase_taps"][tap_name]["tapPosition"]))
                print()
                print()
                """
                prev_value_diff = int(hds_tap["previous_value"]) - int(
                    dwo_taps["phase_taps"][tap_name]["lowTapPosition"]
                )
                after_value_diff = int(hds_tap["after_value"]) - int(
                    dwo_taps["phase_taps"][tap_name]["tapPosition"]
                )
                print("Hades prev")
                print(hds_tap["previous_value"])
                print("Dwo prev")
                print(dwo_taps["phase_taps"][tap_name]["lowTapPosition"])
                print("Hades after")
                print(hds_tap["after_value"])
                print("Dwo after")
                print(dwo_taps["phase_taps"][tap_name]["tapPosition"])
                print()
                print()
                """
        '''

    for tap_name in keys_ratio_not_matching:
        if int(dwo_taps["ratio_taps"][tap_name]["tapPosition"]) != 0:
            print(tap_name)
            print(int(dwo_taps["ratio_taps"][tap_name]["tapPosition"]))

    print()
    print()
    print()
    print()

    # TODO: Treat non matching parts

    """
    for hds_tap in hades_taps:
        print(hds_tap)
        tap_diff_entry = {}
        tap_name = hds_tap["quadripole_name"]

        if tap_name in dwo_taps["phase_taps"].keys():
            print(tap_name)
            prev_value_diff = int(hds_tap["previous_value"]) - int(
                dwo_taps["phase_taps"][tap_name]["lowTapPosition"]
            )
            after_value_diff = int(hds_tap["after_value"]) - int(
                dwo_taps["phase_taps"][tap_name]["tapPosition"]
            )

            tap_diff_entry["previous_value_diff"] = str(abs(prev_value_diff))
            tap_diff_entry["after_value_diff"] = str(abs(after_value_diff))

        elif tap_name in dwo_taps["ratio_taps"].keys():
            print(tap_name)
            prev_value_diff = int(hds_tap["previous_value"]) - int(
                dwo_taps["ratio_taps"][tap_name]["lowTapPosition"]
            )
            after_value_diff = int(hds_tap["after_value"]) - int(
                dwo_taps["ratio_taps"][tap_name]["tapPosition"]
            )

            tap_diff_entry["previous_value_diff"] = str(abs(prev_value_diff))
            tap_diff_entry["after_value_diff"] = str(abs(after_value_diff))

        else:
            print("pepe")

        taps_diffs_dict[tap_name] = tap_diff_entry
    
    return taps_diffs_dict
    """
    return {}


def calc_matching_volt_constr(matched_volt_constr):
    diff_marching_volt = 0

    for case_diffs_list in matched_volt_constr.values():
        for case_diffs in case_diffs_list:
            pass
            # print(case_diffs)
        # print()

    return diff_marching_volt


def calc_matching_flow_constr(matched_flow_constr):
    diff_marching_flow = 0

    for case_diffs_list in matched_flow_constr.values():
        for case_diffs in case_diffs_list:
            pass
            # print(case_diffs)
        # print()

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
        if constr_dwo["modelName"] not in matched_constr:
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
        if "tap_changers" in hades_info[1] and dwo_info["status"] == "CONVERGENCE":
            print(hades_info[1]["name"])
            taps_diff = compare_taps(hades_info[1]["tap_changers"], dwo_info["tap_diffs"])

        # Get constraint diffs
        constraints_diffs = compare_constraints(
            hades_info[1]["constr_volt"],
            hades_info[1]["constr_flow"],
            hades_info[1]["constr_gen_Q"],
            hades_info[1]["constr_gen_U"],
            dwo_info["constraints"],
        )

    return dict_diffs
