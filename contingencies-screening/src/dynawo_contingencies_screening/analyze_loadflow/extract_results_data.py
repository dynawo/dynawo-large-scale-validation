from lxml import etree


def get_contingencies_dict(parsed_hades_input_file):
    # Using a parsed xml, get a dict of all the contingencies that run on it.
    # Return a dict of strings with the identifiers of the contingencies and their data.

    # TODO: add more input data to dict
    root = parsed_hades_input_file.getroot()
    ns = etree.QName(root).namespace

    contingencies_dict = {}
    for variante in root.iter("{%s}variante" % ns):
        contingencies_dict[variante.attrib["num"]] = {"nom": variante.attrib["nom"]}

    return contingencies_dict


def get_voltages(root, ns, contingencies_list):
    # Create the dictionaries where we will store the data
    max_voltages_dict = {key: [] for key in contingencies_list}
    min_voltages_dict = {key: [] for key in contingencies_list}

    for entry in root.iter("{%s}posteSurv" % ns):
        # Store the VMin value and its contingency
        min_voltages_dict[entry.attrib["varianteVmin"]].append(entry.attrib["vmin"])
        # Store the VMax value and its contingency
        max_voltages_dict[entry.attrib["varianteVmax"]].append(entry.attrib["vmax"])

    return min_voltages_dict, max_voltages_dict


def collect_hades_results(contingencies_dict, parsed_hades_output_file):
    # For each of the dict identifiers, insert the information of the result
    # of the contingency found in the outputs

    # TODO: add output data to dict
    root = parsed_hades_output_file.getroot()
    ns = etree.QName(root).namespace

    # Collect the voltages data and its contingencies
    min_voltages_dict, max_voltages_dict = get_voltages(root, ns, list(contingencies_dict.keys()))

    for key in contingencies_dict.keys():
        contingencies_dict[key]["min_voltages"] = min_voltages_dict[key]
        contingencies_dict[key]["max_voltages"] = max_voltages_dict[key]

    return contingencies_dict
