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


def collect_hades_results(contingencies_dict, parsed_hades_output_file):
    # For each of the dict identifiers, insert the information of the result
    # of the contingency found in the outputs

    # TODO: add output data to dict
    root = parsed_hades_output_file.getroot()
    ns = etree.QName(root).namespace

    for key in contingencies_dict.keys():
        contingencies_dict[key]["temp_data"] = "dummy"

    return contingencies_dict
