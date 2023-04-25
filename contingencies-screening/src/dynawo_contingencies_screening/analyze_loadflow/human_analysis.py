from lxml import etree


def analyze_loadflow_resuts(contingencies_dict, parsed_hades_output_file):
    # TODO: Explain what should be done
    # TODO: Implement it

    root = parsed_hades_output_file.getroot()
    ns = etree.QName(root).namespace

    import random

    for key in contingencies_dict.keys():
        contingencies_dict[key]["final_score"] = random.randint(0, 100)

    return contingencies_dict
