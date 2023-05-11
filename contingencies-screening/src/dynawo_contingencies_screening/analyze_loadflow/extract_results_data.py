from lxml import etree


def get_contingencies_dict(parsed_hades_input_file):
    # Using a parsed xml, get a dict of all the contingencies that run on it.
    # Return a dict of strings with the identifiers of the contingencies and their data.

    # TODO: add more input data to dict
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
        }

    return contingencies_dict


def get_voltages(root, ns, contingencies_list):
    # Create the dictionaries where we will store the data
    max_voltages_dict = {key: [] for key in contingencies_list}
    min_voltages_dict = {key: [] for key in contingencies_list}

    for entry in root.iter("{%s}posteSurv" % ns):
        vmin = entry.attrib["vmin"]
        vmax = entry.attrib["vmax"]
        if vmin != vmax:
            # Store the VMin value and its contingency
            min_voltages_dict[entry.attrib["varianteVmin"]].append(vmin)
            # Store the VMax value and its contingency
            max_voltages_dict[entry.attrib["varianteVmax"]].append(vmax)

    return min_voltages_dict, max_voltages_dict


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
        for constraint in load_flow_branch:
            if constraint.tag in [
                "{%s}contrTransit" % ns,
                "{%s}contrTension" % ns,
                "{%s}contrGroupe" % ns,
            ]:
                constraint_entry = {
                    "job": constraint.attrib["ouvrage"],
                    "before": constraint.attrib["avant"],
                    "after": constraint.attrib["apres"],
                    "limit": constraint.attrib["limite"],
                }

                # Check for the constraint type
                if constraint.tag == ("{%s}contrGroupe" % ns):
                    constraint_entry["typeLim"] = int(constraint.attrib["typeLim"])
                    constraint_entry["type"] = constraint.attrib["type"]
                    constraint_dict["contrGroupe"][contingency_number].append(constraint_entry)
                elif constraint.tag == ("{%s}contrTransit" % ns):
                    constraint_entry["tempo"] = constraint.attrib["tempo"]
                    constraint_entry["beforeMW"] = constraint.attrib["avantMW"]
                    constraint_entry["afterMW"] = constraint.attrib["apresMW"]
                    constraint_entry["sideOr"] = constraint.attrib["coteOr"]
                    constraint_dict["contrTransit"][contingency_number].append(constraint_entry)
                else:
                    constraint_entry["threshType"] = constraint.attrib["typeSeuil"]
                    constraint_entry["tempo"] = constraint.attrib["tempo"]
                    constraint_dict["contrTension"][contingency_number].append(constraint_entry)

    return (
        status_dict,
        cause_dict,
        iter_number_dict,
        calc_duration_dict,
        constraint_dict,
    )


def collect_hades_results(contingencies_dict, parsed_hades_output_file):
    # For each of the dict identifiers, insert the information of the result
    # of the contingency found in the outputs

    # Get the root and the namespacing of the file
    root = parsed_hades_output_file.getroot()
    ns = etree.QName(root).namespace

    # Collect the voltages data and its contingencies
    min_voltages_dict, max_voltages_dict = get_voltages(root, ns, list(contingencies_dict.keys()))

    # TODO: Get poste voltages in order to compute continuous score

    # Collect all the 'defaut' tag data
    (
        status_dict,
        cause_dict,
        iter_number_dict,
        calc_duration_dict,
        constraint_dict,
    ) = get_fault_data(root, ns, list(contingencies_dict.keys()))

    for key in contingencies_dict.keys():
        contingencies_dict[key]["min_voltages"] = min_voltages_dict[key]
        contingencies_dict[key]["max_voltages"] = max_voltages_dict[key]
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

    return contingencies_dict
