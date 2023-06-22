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


def get_tap_score_diff(tap1_diff, tap2_diff, lim1, lim2, block1, block2):

    diff_score = 0
    weight_diff = 10

    # Get a score for tap diffs movement
    if (
        (tap1_diff < 0 and tap2_diff > 0)
        or (tap1_diff > 0 and tap2_diff < 0)
        or (tap1_diff < 0 and tap2_diff == 0)
        or (tap1_diff == 0 and tap2_diff < 0)
        or (tap1_diff > 0 and tap2_diff == 0)
        or (tap1_diff == 0 and tap2_diff > 0)
    ):
        diff_score += (abs(tap1_diff) + abs(tap2_diff)) * 2 * weight_diff

    elif (tap1_diff < 0 and tap2_diff < 0) or (tap1_diff > 0 and tap2_diff > 0):
        diff_score += abs(abs(tap1_diff) - abs(tap2_diff)) * weight_diff

    elif tap1_diff == 0 and tap2_diff == 0:
        diff_score += 0

    else:
        print("Warning, tap diff case not contemplated.")

    # Add to the movement difference score if the taps have been saturated or not
    if (lim1 and not lim2) or (not lim1 and lim2):
        diff_score += 1 * weight_diff

    elif lim1 and lim2:
        if (tap1_diff < 0 and tap2_diff > 0) or (tap1_diff > 0 and tap2_diff < 0):
            diff_score += 3 * weight_diff
        elif (tap1_diff < 0 and tap2_diff < 0) or (tap1_diff > 0 and tap2_diff > 0):
            diff_score += 0.5 * weight_diff
        else:
            print("Warning, tap diff lim case not contemplated.")

    elif not lim1 and not lim2:
        diff_score += 0

    else:
        print("Warning, tap diff lim case not contemplated.")

    # Add to movement difference score whether or not taps have been blocked
    if (block1 and not block2) or (not block1 and block2):
        diff_score += 5 * weight_diff

    elif block1 and block2:
        diff_score += 1 * weight_diff

    elif not block1 and not block2:
        diff_score += 0

    else:
        print("Warning, tap diff block case not contemplated.")

    return diff_score


def compare_taps(hades_taps, dwo_taps):

    # Matching of the contingencies and their names to later get a score based
    # on the changes they have undergone
    final_tap_score = 0

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

    print("matching_keys - matching_keys - matching_keys - matching_keys - matching_keys")
    for matching_key in matching_keys:
        if matching_key in dwo_taps["phase_taps"]:
            dwo_diff = dwo_taps["phase_taps"][matching_key]
        elif matching_key in dwo_taps["ratio_taps"]:
            dwo_diff = dwo_taps["ratio_taps"][matching_key]

        hds_tap = {}
        for hds_tap_ent in hades_taps:
            if hds_tap_ent["quadripole_name"] == matching_key:
                hds_tap = hds_tap_ent
                break

        hds_diff = hds_tap["diff_value"]
        lim_hds = False
        block_hds = False
        if int(hds_tap["stopper"]) == 2 or int(hds_tap["stopper"]) == 1:
            lim_hds = True
        elif int(hds_tap["stopper"]) == 3:
            block_hds = True

        # TODO: get block and lim dwo
        final_tap_score += get_tap_score_diff(hds_diff, dwo_diff, lim_hds, False, block_hds, False)

        print(matching_key)
        print(hds_diff, dwo_diff)

    print(
        "keys_hades_not_matching - keys_hades_not_matching - keys_hades_not_matching - keys_hades_not_matching - keys_hades_not_matching"
    )
    for hades_key in keys_hades_not_matching:
        hds_tap = {}
        for hds_tap_ent in hades_taps:
            if hds_tap_ent["quadripole_name"] == hades_key:
                hds_tap = hds_tap_ent
                break

        hds_diff = hds_tap["diff_value"]
        lim_hds = False
        block_hds = False
        if int(hds_tap["stopper"]) == 2 or int(hds_tap["stopper"]) == 1:
            lim_hds = True
        elif int(hds_tap["stopper"]) == 3:
            block_hds = True

        final_tap_score += get_tap_score_diff(hds_diff, 0, lim_hds, False, block_hds, False)

        print(hades_key)
        print(hds_diff, 0)

    print(
        "keys_phase_not_matching - keys_phase_not_matching - keys_phase_not_matching - keys_phase_not_matching - keys_phase_not_matching"
    )
    for dwo_key in keys_phase_not_matching:
        dwo_diff = dwo_taps["phase_taps"][dwo_key]

        # TODO: get block and lim dwo
        final_tap_score += get_tap_score_diff(0, dwo_diff, False, False, False, False)
        print(dwo_key)
        print(0, dwo_diff)

    print(
        "keys_ratio_not_matching - keys_ratio_not_matching - keys_ratio_not_matching - keys_ratio_not_matching - keys_ratio_not_matching"
    )
    for dwo_key in keys_ratio_not_matching:
        dwo_diff = dwo_taps["ratio_taps"][dwo_key]

        # TODO: get block and lim dwo
        final_tap_score += get_tap_score_diff(0, dwo_diff, False, False, False, False)

        print(dwo_key)
        print(0, dwo_diff)

    print(final_tap_score)
    print()

    return final_tap_score


def calc_volt_constr(matched_volt_constr, unique_constr_hds, unique_constr_dwo):
    diff_score_volt = 0

    weight_diff = 20

    # TODO: Check double constraints
    # TODO: Evaluate other options
    print("calc_volt_constr")
    for case_diffs_list in matched_volt_constr.values():
        for case_diffs in case_diffs_list:
            print(case_diffs[0]["typeSeuil"], case_diffs[1]["kind"])
            if int(case_diffs[0]["typeSeuil"]) == 1 and case_diffs[1]["kind"] == "UInfUmin":
                diff_score_volt += weight_diff * 1
            elif int(case_diffs[0]["typeSeuil"]) == 1 and case_diffs[1]["kind"] == "USupUmax":
                diff_score_volt += weight_diff * 5
            elif int(case_diffs[0]["typeSeuil"]) == 0 and case_diffs[1]["kind"] == "UInfUmin":
                diff_score_volt += weight_diff * 5
            elif int(case_diffs[0]["typeSeuil"]) == 0 and case_diffs[1]["kind"] == "USupUmax":
                diff_score_volt += weight_diff * 1
            else:
                print("Volt constraint type not matched.")

    for case_diffs in unique_constr_hds:
        weight_diff += weight_diff * 3
    for case_diffs in unique_constr_dwo:
        weight_diff += weight_diff * 3

    return diff_score_volt


def calc_flow_constr(matched_flow_constr, unique_constr_hds, unique_constr_dwo):
    diff_score_flow = 0

    weight_diff = 20

    # TODO: Check double constraints
    # TODO: Evaluate other options
    print("calc_flow_constr")
    for case_diffs_list in matched_flow_constr.values():
        for case_diffs in case_diffs_list:
            print(case_diffs[1]["kind"])
            if case_diffs[1]["kind"] == "OverloadUp":
                if (case_diffs[0]["sideOr"] == "true" and int(case_diffs[1]["side"]) == 1) or (
                    case_diffs[0]["sideOr"] == "false" and int(case_diffs[1]["side"]) == 2
                ):
                    diff_score_flow += weight_diff * 1
                else:
                    diff_score_flow += weight_diff * 4
                    print("Different side", case_diffs[0]["sideOr"], case_diffs[1]["side"])
            elif case_diffs[1]["kind"] == "OverloadOpen":
                if (case_diffs[0]["sideOr"] == "true" and int(case_diffs[1]["side"]) == 1) or (
                    case_diffs[0]["sideOr"] == "false" and int(case_diffs[1]["side"]) == 2
                ):
                    diff_score_flow += weight_diff * 3
                else:
                    diff_score_flow += weight_diff * 4
                    print("Different side", case_diffs[0]["sideOr"], case_diffs[1]["side"])
            elif case_diffs[1]["kind"] == "PATL":
                if (case_diffs[0]["sideOr"] == "true" and int(case_diffs[1]["side"]) == 1) or (
                    case_diffs[0]["sideOr"] == "false" and int(case_diffs[1]["side"]) == 2
                ):
                    diff_score_flow += weight_diff * 3
                else:
                    diff_score_flow += weight_diff * 4
                    print("Different side", case_diffs[0]["sideOr"], case_diffs[1]["side"])
            else:
                print("flow constraint type not matched.")

    for case_diffs in unique_constr_hds:
        weight_diff += weight_diff * 3
    for case_diffs in unique_constr_dwo:
        weight_diff += weight_diff * 3

    return diff_score_flow


def calc_gen_Q_constr(matched_gen_Q_constr, unique_constr_hds, unique_constr_dwo):
    diff_score_gen_Q = 0

    weight_diff = 20

    # TODO: Check double constraints
    # TODO: Evaluate other options
    print("calc_gen_Q_constr")
    for case_diffs_list in matched_gen_Q_constr.values():
        for case_diffs in case_diffs_list:
            print(case_diffs[0]["typeLim"], case_diffs[1]["kind"])
            if int(case_diffs[0]["typeLim"]) == 1 and case_diffs[1]["kind"] == "QInfQMin":
                diff_score_gen_Q += weight_diff * 1
            elif int(case_diffs[0]["typeLim"]) == 1 and case_diffs[1]["kind"] == "QSupQMax":
                diff_score_gen_Q += weight_diff * 5
            elif int(case_diffs[0]["typeLim"]) == 0 and case_diffs[1]["kind"] == "QInfQMin":
                diff_score_gen_Q += weight_diff * 5
            elif int(case_diffs[0]["typeLim"]) == 0 and case_diffs[1]["kind"] == "QSupQMax":
                diff_score_gen_Q += weight_diff * 1
            else:
                print("gen_Q constraint type not matched.")

    for case_diffs in unique_constr_hds:
        weight_diff += weight_diff * 3
    for case_diffs in unique_constr_dwo:
        weight_diff += weight_diff * 3

    return diff_score_gen_Q


def calc_gen_U_constr(matched_gen_U_constr, unique_constr_hds, unique_constr_dwo):
    diff_score_gen_U = 0
    # TODO: Implement it
    return diff_score_gen_U


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
        if constraint["kind"] == "UInfUmin" or constraint["kind"] == "USupUmax":
            dwo_volt_constraints.append(constraint)
        elif (
            constraint["kind"] == "PATL"
            or constraint["kind"] == "OverloadOpen"
            or constraint["kind"] == "OverloadUp"
        ):
            dwo_flow_constraints.append(constraint)
        elif constraint["kind"] == "QInfQMin" or constraint["kind"] == "QSupQMax":
            dwo_gen_Q_constraints.append(constraint)
        # TODO: Change this condition
        elif constraint["kind"] == "Pending":
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

    diff_score_volt = calc_volt_constr(
        matched_volt_constr, unique_constr_volt_hds, unique_constr_volt_dwo
    )
    diff_score_flow = calc_flow_constr(
        matched_flow_constr, unique_constr_flow_hds, unique_constr_flow_dwo
    )
    diff_score_gen_Q = calc_gen_Q_constr(
        matched_gen_Q_constr, unique_constr_gen_Q_hds, unique_constr_gen_Q_dwo
    )
    diff_score_gen_U = calc_gen_U_constr(
        matched_gen_U_constr, unique_constr_gen_U_hds, unique_constr_gen_U_dwo
    )
    print(diff_score_volt + diff_score_flow + diff_score_gen_Q + diff_score_gen_U)
    return diff_score_volt + diff_score_flow + diff_score_gen_Q + diff_score_gen_U


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

        dict_diffs["diff_value"] = abs(taps_diff) + abs(constraints_diffs)

    return [dict_diffs["conv_status"], dict_diffs["diff_value"]]
