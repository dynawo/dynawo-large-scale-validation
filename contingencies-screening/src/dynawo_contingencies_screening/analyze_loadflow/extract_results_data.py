from lxml import etree
from dynawo_contingencies_screening.commons import manage_files


def get_elements_dict(parsed_hades_input_file):
    # Using a parsed xml, get a dict of all the elements that run on it.
    # Return a dict of strings with the identifiers of the elements and their data.

    root = parsed_hades_input_file.getroot()
    ns = etree.QName(root).namespace

    elements_dict = {}

    poste_dict = {}
    for poste in root.iter("{%s}poste" % ns):
        poste_dict[int(poste.attrib["num"])] = {
            "nom": poste.attrib["nom"],
            "unom": poste.attrib["unom"],
            "volt_level": int(poste.attrib["nivTension"]),
        }

    noeud_dict = {}
    for noeud in root.iter("{%s}noeud" % ns):
        noeud_dict[int(noeud.attrib["num"])] = {
            "nom": noeud.attrib["nom"],
            "poste": noeud.attrib["poste"],
            "vmax": noeud.attrib["vmax"],
            "vmin": noeud.attrib["vmin"],
            "volt_level": poste_dict[int(noeud.attrib["poste"])]["volt_level"]
            if int(noeud.attrib["poste"]) in poste_dict
            else None,
        }

    groupe_dict = {}
    for groupe in root.iter("{%s}groupe" % ns):
        groupe_dict[int(groupe.attrib["num"])] = {
            "nom": groupe.attrib["nom"],
            "poste": groupe.attrib["poste"],
            "noeud": groupe.attrib["noeud"],
            "pmax": groupe.attrib["pmax"],
            "pmin": groupe.attrib["pmin"],
            "volt_level": poste_dict[int(groupe.attrib["poste"])]["volt_level"]
            if int(groupe.attrib["poste"]) in poste_dict
            else None,
        }

    conso_dict = {}
    for conso in root.iter("{%s}conso" % ns):
        conso_dict[int(conso.attrib["num"])] = {
            "nom": conso.attrib["nom"],
            "poste": conso.attrib["poste"],
            "noeud": conso.attrib["noeud"],
            "volt_level": poste_dict[int(conso.attrib["poste"])]["volt_level"]
            if int(conso.attrib["poste"]) in poste_dict
            else None,
        }

    shunt_dict = {}
    for shunt in root.iter("{%s}shunt" % ns):
        shunt_dict[int(shunt.attrib["num"])] = {
            "nom": shunt.attrib["nom"],
            "poste": shunt.attrib["poste"],
            "noeud": shunt.attrib["noeud"],
            "volt_level": poste_dict[int(shunt.attrib["poste"])]["volt_level"]
            if int(shunt.attrib["poste"]) in poste_dict
            else None,
        }

    quadripole_dict = {}
    for quadripole in root.iter("{%s}quadripole" % ns):
        quadripole_dict[int(quadripole.attrib["num"])] = {
            "nom": quadripole.attrib["nom"],
            "absnor": quadripole.attrib["absnor"],
            "absnex": quadripole.attrib["absnex"],
            "nor": quadripole.attrib["nor"],
            "nex": quadripole.attrib["nex"],
            "postor": quadripole.attrib["postor"],
            "postex": quadripole.attrib["postex"],
            "resistance": quadripole.attrib["resistance"],
            "reactance": quadripole.attrib["reactance"],
            "volt_level": poste_dict[int(quadripole.attrib["postor"])]["volt_level"]
            if int(quadripole.attrib["postor"]) in poste_dict
            else None,
        }

    elements_dict["poste"] = poste_dict
    elements_dict["noeud"] = noeud_dict
    elements_dict["groupe"] = groupe_dict
    elements_dict["conso"] = conso_dict
    elements_dict["shunt"] = shunt_dict
    elements_dict["quadripole"] = quadripole_dict

    return elements_dict


def get_contingencies_dict(parsed_hades_input_file):
    # Using a parsed xml, get a dict of all the contingencies that run on it.
    # Return a dict of strings with the identifiers of the contingencies and their data.

    root = parsed_hades_input_file.getroot()
    ns = etree.QName(root).namespace

    contingencies_dict = {}
    for variante in root.iter("{%s}variante" % ns):
        affected_elements_list = []
        for quadex in variante.iter("{%s}quadex" % ns):
            affected_elements_list.append(quadex.text)
        for quador in variante.iter("{%s}quador" % ns):
            affected_elements_list.append(quador.text)
        for ouvrage in variante.iter("{%s}ouvrage" % ns):
            affected_elements_list.append(ouvrage.attrib["num"])
        for vscor in variante.iter("{%s}vscor" % ns):
            affected_elements_list.append(vscor.text)

        contingencies_dict[variante.attrib["num"]] = {
            "name": variante.attrib["nom"],
            "type": int(variante.attrib["type"]),
            "affected_elements": affected_elements_list,
            "coefrepquad": int(variante.attrib["coefrepquad"]),
        }

    return contingencies_dict


def get_max_min_voltages(root, ns, contingencies_list):
    # Create the dictionaries where the data will be stored
    max_voltages_dict = {key: [] for key in contingencies_list}
    min_voltages_dict = {key: [] for key in contingencies_list}
    poste_node_volt_dict = {}

    for entry in root.iter("{%s}posteSurv" % ns):
        poste_node_volt_dict[int(entry.attrib["poste"])] = int(entry.attrib["noeud"])
        vmin = float(entry.attrib["vmin"])
        vmax = float(entry.attrib["vmax"])
        if vmin != vmax:
            # Store the VMin value and its contingency
            min_voltages_dict[entry.attrib["varianteVmin"]].append(
                [int(entry.attrib["poste"]), vmin]
            )
            # Store the VMax value and its contingency
            max_voltages_dict[entry.attrib["varianteVmax"]].append(
                [int(entry.attrib["poste"]), vmax]
            )

    return min_voltages_dict, max_voltages_dict, poste_node_volt_dict


def get_poste_node_voltages(root, ns, elements_dict, poste_node_volt_dict):
    # Add all the voltage values for each of the nodes and "denormalize" it.
    # Once this is done, define these voltages for each of the postes
    for noeud in root.iter("{%s}noeud" % ns):
        variable = noeud.find("{%s}variables" % ns)
        # Convert voltage value from base 100 to real value
        elements_dict["noeud"][int(noeud.attrib["num"])]["volt"] = (
            float(variable.attrib["v"])
            * float(
                elements_dict["poste"][
                    int(elements_dict["noeud"][int(noeud.attrib["num"])]["poste"])
                ]["unom"]
            )
        ) / 100

    for poste, node in poste_node_volt_dict.items():
        elements_dict["poste"][poste]["volt"] = elements_dict["noeud"][node]["volt"]

    return elements_dict


def get_line_flows(root, ns, contingencies_dict):
    invert_dict = {}

    for contg in contingencies_dict.keys():
        if contingencies_dict[contg]["coefrepquad"] not in invert_dict:
            invert_dict[contingencies_dict[contg]["coefrepquad"]] = contg
        else:
            exit("Ill-defined coefrepquad contingencies")

    # Create the dictionaries where the data will be stored
    line_flows_dict = {key: [] for key in contingencies_dict.keys()}

    for entry in root.iter("{%s}resChargeMax" % ns):
        line_flows_dict[invert_dict[int(entry.attrib["quadripole"])]].append(
            [int(entry.attrib["numOuvrSurv"]), float(entry.attrib["chargeMax"])]
        )

    return line_flows_dict


def get_fault_data(root, ns, contingencies_list):
    # Create the dictionaries where we will store the data
    status_dict = {}
    cause_dict = {}
    iter_number_dict = {}
    calc_duration_dict = {}
    constraint_dict = {}
    constraint_dict["contrTransit"] = {key: [] for key in contingencies_list}
    constraint_dict["contrTension"] = {key: [] for key in contingencies_list}
    constraint_dict["contrGroupe"] = {key: [] for key in contingencies_list}
    coef_report_dict = {key: [] for key in contingencies_list}
    res_node_dict = {key: [] for key in contingencies_list}
    tap_changers_dict = {key: [] for key in contingencies_list}

    groupe_name = {}
    for groupe in root.iter("{%s}groupe" % ns):
        groupe_name[int(groupe.attrib["num"])] = groupe.attrib["nom"]

    quadripole_name = {}
    for quadripole in root.iter("{%s}quadripole" % ns):
        quadripole_name[int(quadripole.attrib["num"])] = quadripole.attrib["nom"]

    node_name = {}
    for node in root.iter("{%s}noeud" % ns):
        node_name[int(node.attrib["num"])] = node.attrib["nom"]

    for contingency in root.iter("{%s}defaut" % ns):
        # Collect the data from the 'resLF' tag
        contingency_number = contingency.attrib["num"]
        load_flow_branch = contingency.find("{%s}resLF" % ns)
        status_dict[contingency_number] = int(load_flow_branch.attrib["statut"])
        cause_dict[contingency_number] = int(load_flow_branch.attrib["cause"])
        iter_number_dict[contingency_number] = int(load_flow_branch.attrib["nbIter"])
        calc_duration_dict[contingency_number] = round(
            float(load_flow_branch.attrib["dureeCalcul"]), 5
        )

        # Collect the constraints data
        for subelement in load_flow_branch:
            if subelement.tag in [
                "{%s}contrTransit" % ns,
                "{%s}contrTension" % ns,
                "{%s}contrGroupe" % ns,
            ]:
                constraint_entry = {
                    "elem_num": int(subelement.attrib["ouvrage"]),
                    "before": subelement.attrib["avant"],
                    "after": subelement.attrib["apres"],
                    "limit": subelement.attrib["limite"],
                }

                # Check for the constraint type
                if subelement.tag == ("{%s}contrGroupe" % ns):
                    constraint_entry["elem_name"] = groupe_name[constraint_entry["elem_num"]]
                    constraint_entry["typeLim"] = int(subelement.attrib["typeLim"])
                    constraint_entry["type"] = subelement.attrib["type"]
                    constraint_dict["contrGroupe"][contingency_number].append(constraint_entry)
                elif subelement.tag == ("{%s}contrTransit" % ns):
                    constraint_entry["elem_name"] = quadripole_name[constraint_entry["elem_num"]]
                    constraint_entry["tempo"] = subelement.attrib["tempo"]
                    constraint_entry["beforeMW"] = subelement.attrib["avantMW"]
                    constraint_entry["afterMW"] = subelement.attrib["apresMW"]
                    constraint_entry["sideOr"] = subelement.attrib["coteOr"]
                    constraint_dict["contrTransit"][contingency_number].append(constraint_entry)
                else:
                    constraint_entry["elem_name"] = node_name[constraint_entry["elem_num"]]
                    constraint_entry["threshType"] = subelement.attrib["typeSeuil"]
                    constraint_entry["tempo"] = subelement.attrib["tempo"]
                    constraint_dict["contrTension"][contingency_number].append(constraint_entry)
            # Get all coefReport entries
            elif subelement.tag == "{%s}coefReport" % ns:
                report_entry = {}

                report_entry["num"] = subelement.attrib["num"]
                report_entry["coefAmpere"] = subelement.attrib["coefAmpere"]
                report_entry["coefMW"] = subelement.attrib["coefMW"]
                report_entry["transitActN"] = subelement.attrib["transitActN"]
                report_entry["transitAct"] = subelement.attrib["transitAct"]
                report_entry["intensityN"] = subelement.attrib["intensiteN"]
                report_entry["intensity"] = subelement.attrib["intensite"]
                report_entry["charge"] = subelement.attrib["charge"]
                report_entry["threshold"] = subelement.attrib["seuil"]
                report_entry["sideOr"] = subelement.attrib["coteOr"]

                coef_report_dict[contingency_number].append(report_entry)
            # Get all resNoeud entries
            elif subelement.tag == "{%s}resnoeud" % ns:
                node_entry = {"quadripole_num": subelement.attrib["numOuvrSurv"]}
                res_node_dict[contingency_number].append(node_entry)
            # Get all resregleur entries
            elif subelement.tag == "{%s}resregleur" % ns:
                tap_entry = {}
                gen_name = ""

                # Get the tap's generator name
                for gen in root.iter("{%s}quadripole" % ns):
                    if gen.attrib["num"] == subelement.attrib["numOuvrSurv"]:
                        gen_name = gen.attrib["nom"]

                tap_entry["quadripole_num"] = subelement.attrib["numOuvrSurv"]
                tap_entry["quadripole_name"] = gen_name
                tap_entry["previous_value"] = subelement.attrib["priseDeb"]
                tap_entry["after_value"] = subelement.attrib["priseFin"]
                tap_entry["diff_value"] = int(subelement.attrib["priseFin"]) - int(
                    subelement.attrib["priseDeb"]
                )

                tap_entry["stopper"] = subelement.attrib["butee"]

                tap_changers_dict[contingency_number].append(tap_entry)

    return (
        status_dict,
        cause_dict,
        iter_number_dict,
        calc_duration_dict,
        constraint_dict,
        coef_report_dict,
        res_node_dict,
        tap_changers_dict,
    )


def collect_hades_results(
    elements_dict, contingencies_dict, parsed_hades_output_file, tap_changers
):
    # For each of the dict identifiers, insert the information of the result
    # of the contingency found in the outputs

    # Get the root and the namespacing of the file
    root = parsed_hades_output_file.getroot()
    ns = etree.QName(root).namespace

    # Collect the voltages data and its contingencies
    min_voltages_dict, max_voltages_dict, poste_node_volt_dict = get_max_min_voltages(
        root, ns, list(contingencies_dict.keys())
    )

    # Get poste voltages in order to compute continuous score
    elements_dict = get_poste_node_voltages(root, ns, elements_dict, poste_node_volt_dict)

    # Collect flow data and its contingencies
    line_flows_dict = get_line_flows(root, ns, contingencies_dict)

    # Collect all the 'defaut' tag data
    (
        status_dict,
        cause_dict,
        iter_number_dict,
        calc_duration_dict,
        constraint_dict,
        coef_report_dict,
        res_node_dict,
        tap_changers_dict,
    ) = get_fault_data(root, ns, list(contingencies_dict.keys()))

    for key in contingencies_dict.keys():
        contingencies_dict[key]["min_voltages"] = min_voltages_dict[key]
        contingencies_dict[key]["max_voltages"] = max_voltages_dict[key]
        contingencies_dict[key]["max_flow"] = line_flows_dict[key]
        contingencies_dict[key]["status"] = status_dict[key]
        contingencies_dict[key]["cause"] = cause_dict[key]
        contingencies_dict[key]["n_iter"] = iter_number_dict[key]
        contingencies_dict[key]["calc_duration"] = calc_duration_dict[key]
        contingencies_dict[key]["constr_volt"] = constraint_dict["contrTension"][key]
        contingencies_dict[key]["constr_flow"] = constraint_dict["contrTransit"][key]

        constr_gen_Q = [
            constr_i
            for constr_i in constraint_dict["contrGroupe"][key]
            if constr_i["typeLim"] == 0 or constr_i["typeLim"] == 1
        ]
        constr_gen_U = [
            constr_i
            for constr_i in constraint_dict["contrGroupe"][key]
            if constr_i["typeLim"] == 2 or constr_i["typeLim"] == 3
        ]
        contingencies_dict[key]["constr_gen_Q"] = constr_gen_Q
        contingencies_dict[key]["constr_gen_U"] = constr_gen_U
        contingencies_dict[key]["coef_report"] = coef_report_dict[key]
        contingencies_dict[key]["res_node"] = res_node_dict[key]

        # Skip tap_changers dictionary if option is not activated
        if tap_changers:
            contingencies_dict[key]["tap_changers"] = tap_changers_dict[key]

    return elements_dict, contingencies_dict


def get_dynawo_contingencies(dynawo_xml_root, ns, contg_set):
    contingencies_dict = {}

    for contg in dynawo_xml_root.iter("{%s}scenarioResults" % ns):
        contg_id = contg.attrib["id"]
        if contg_id in contg_set:
            contingencies_dict[contg_id] = {"status": contg.attrib["status"], "constraints": []}

    return contingencies_dict


def get_dynawo_timeline_constraints(root, ns, dwo_constraint_list):
    # Reverse the timeline events
    timeline = root.findall("{%s}event" % ns)
    timeline = list(reversed(timeline))

    checked_models = set()

    for entry in timeline:
        # Check if model name is in checked elements
        if entry.attrib["modelName"] in checked_models:
            continue
        else:
            checked_models.add(entry.attrib["modelName"])

            # Look for the "Generator : min/max reactive power limit reached
            if (entry.attrib["message"] == "Generator : minimum reactive power limit reached") or (
                entry.attrib["message"] == "Generator : maximum reactive power limit reached"
            ):
                limit_constr = {}

                limit_constr["modelName"] = entry.attrib["modelName"]

                # Create the description from the timelimit message
                if "minimum" in entry.attrib["message"]:
                    limit_constr["description"] = "min Q limit reached"
                    limit_constr["kind"] = "QInfQMin"
                else:
                    limit_constr["description"] = "max Q limit reached"
                    limit_constr["kind"] = "QSupQMax"

                limit_constr["time"] = entry.attrib["time"]
                limit_constr["type"] = "Generator"

                dwo_constraint_list.append(limit_constr)

    return dwo_constraint_list


def get_dynawo_contingency_data(
    dynawo_contingencies_dict, dynawo_nocontg_tap_dict, dynawo_output_folder
):
    # Check results of all the contingencies
    for contg in dynawo_contingencies_dict.keys():
        # Get the contingency data from converged contingencies
        if dynawo_contingencies_dict[contg]["status"] == "CONVERGENCE":
            # Get the contingency constraints file path
            constraints_file_name = "constraints_" + contg + ".xml"
            constraints_file = dynawo_output_folder / "constraints" / constraints_file_name

            # Parse the constraints file
            parsed_constraints_file = manage_files.parse_xml_file(constraints_file)

            # Get the root and the namespacing of the file
            root = parsed_constraints_file.getroot()
            ns = etree.QName(root).namespace

            # Extract the constraint data
            for entry in root.iter("{%s}constraint" % ns):
                # Add the constraint data to main dictionary
                dynawo_contingencies_dict[contg]["constraints"].append(entry.attrib)

            # Get the contingency timeline file path
            timeline_file_name = "timeline_" + contg + ".xml"
            timeline_file = dynawo_output_folder / "timeLine" / timeline_file_name

            # Parse the timeline file
            parsed_timeline_file = manage_files.parse_xml_file(timeline_file)

            # Get the root and the namespacing of the file
            root = parsed_timeline_file.getroot()
            ns = etree.QName(root).namespace

            # Extract the timeline constraint data
            dynawo_contingencies_dict[contg]["constraints"] = get_dynawo_timeline_constraints(
                root, ns, dynawo_contingencies_dict[contg]["constraints"]
            )

            # Get the contingency output file for the tap data
            contg_output_file = (
                dynawo_output_folder / contg / "outputs" / "finalState" / "outputIIDM.xml"
            )

            # Parse the output file
            parsed_output_file = manage_files.parse_xml_file(contg_output_file)

            # Get the root and the namespacing of the file
            root = parsed_output_file.getroot()
            ns = etree.QName(root).namespace

            # Extract the contingency tap data to the main contingency dict
            dynawo_contingencies_dict[contg]["tap_changers"] = get_dynawo_tap_data(root, ns)

            # Compare taps with no contingency case
            get_dynawo_tap_diffs(dynawo_contingencies_dict, dynawo_nocontg_tap_dict, contg)


def get_dynawo_tap_data(output_file_root, ns):
    # Create the tap data dictionary
    dynawo_taps_dict = {"phase_taps": {}, "ratio_taps": {}}

    # Extract the tap data depending on its type
    for phase_tap in output_file_root.iter("{%s}phaseTapChanger" % ns):
        phase_tap_dict = {}

        # Get the associated transformer id
        phase_tap_parent = phase_tap.getparent()
        phase_tap_transformer_id = phase_tap_parent.attrib["id"]

        # Add the tap attributes
        phase_tap_dict.update(phase_tap.attrib)

        """
        # Get all nested data
        phase_tap_dict["step"] = []
        for element in phase_tap.iter():
            # Skip element if it is the root
            if element is not phase_tap:
                # Watch for elements different from step
                if element.tag != "{%s}step" % ns:
                    phase_tap_dict["terminalRef"] = element.attrib
                else:
                    phase_tap_dict["step"].append(element.attrib)
        """

        # Add entry to main dictionary
        dynawo_taps_dict["phase_taps"][phase_tap_transformer_id] = phase_tap_dict

    for ratio_tap in output_file_root.iter("{%s}ratioTapChanger" % ns):
        ratio_tap_dict = {}

        # Get the associated transformer id
        ratio_tap_parent = ratio_tap.getparent()
        ratio_tap_transformer_id = ratio_tap_parent.attrib["id"]

        # Add the tap attributes
        ratio_tap_dict.update(ratio_tap.attrib)

        """
        # Get all nested data
        ratio_tap_dict["step"] = []
        for element in ratio_tap.iter():
            # Skip element if it is the root
            if element is not ratio_tap:
                # Watch for elements different from step
                if element.tag != "{%s}step" % ns:
                    ratio_tap_dict["terminalRef"] = element.attrib
                else:
                    ratio_tap_dict["step"].append(element.attrib)
        """

        # Add entry to main dictionary
        dynawo_taps_dict["ratio_taps"][ratio_tap_transformer_id] = ratio_tap_dict

    return dynawo_taps_dict


def get_dynawo_tap_diffs(dynawo_contingencies_dict, dynawo_nocontg_tap_dict, contingency_name):
    tap_diff_dict = {"phase_taps": {}, "ratio_taps": {}}

    # Differences between phase_taps
    # Will be calculated as contg_tap_value - nocontg_tap_value
    for phase_tap_id in dynawo_contingencies_dict[contingency_name]["tap_changers"][
        "phase_taps"
    ].keys():
        contg_phase_tap = dynawo_contingencies_dict[contingency_name]["tap_changers"][
            "phase_taps"
        ][phase_tap_id]

        if phase_tap_id in dynawo_nocontg_tap_dict["phase_taps"]:
            nocontg_phase_tap = dynawo_nocontg_tap_dict["phase_taps"][phase_tap_id]
            phase_tap_diff = int(contg_phase_tap["tapPosition"]) - int(
                nocontg_phase_tap["tapPosition"]
            )

            if phase_tap_diff != 0:
                tap_diff_dict["phase_taps"][phase_tap_id] = phase_tap_diff

    # Differences between ratio_taps
    # Will be calculated as contg_tap_value - nocontg_tap_value
    for ratio_tap_id in dynawo_contingencies_dict[contingency_name]["tap_changers"][
        "ratio_taps"
    ].keys():
        contg_ratio_tap = dynawo_contingencies_dict[contingency_name]["tap_changers"][
            "ratio_taps"
        ][ratio_tap_id]

        if ratio_tap_id in dynawo_nocontg_tap_dict["ratio_taps"]:
            nocontg_ratio_tap = dynawo_nocontg_tap_dict["ratio_taps"][ratio_tap_id]
            ratio_tap_diff = int(contg_ratio_tap["tapPosition"]) - int(
                nocontg_ratio_tap["tapPosition"]
            )

            if ratio_tap_diff != 0:
                tap_diff_dict["ratio_taps"][ratio_tap_id] = ratio_tap_diff

    dynawo_contingencies_dict[contingency_name]["tap_diffs"] = tap_diff_dict


def collect_dynawo_results(parsed_output_xml, parsed_aggregated_xml, dynawo_output_dir, contg_set):
    # Get the root and the namespacing of the output file without contingencies
    root = parsed_output_xml.getroot()
    ns = etree.QName(root).namespace

    # Extract all the tap changer data from de output loadflow without contingencies
    dynawo_nocont_tap_dict = get_dynawo_tap_data(root, ns)

    # Get the root and the namespacing of the aggregated file
    root = parsed_aggregated_xml.getroot()
    ns = etree.QName(root).namespace

    # Create the contingencies dictionary
    dynawo_contingencies_dict = get_dynawo_contingencies(root, ns, contg_set)

    # Extract all the contingencies data
    get_dynawo_contingency_data(
        dynawo_contingencies_dict, dynawo_nocont_tap_dict, dynawo_output_dir
    )

    return dynawo_contingencies_dict, dynawo_nocont_tap_dict
