from lxml import etree
from dynawo_contingencies_screening.commons import manage_files


BRANCH_DISCONNECTION_MODE = "TO"


def generate_branch_contingency(root, element_name):
    # Start by looking for the element entry
    hades_branch = None
    reseau = root.find("./reseau", root.nsmap)
    donneesGroupes = reseau.find("./donneesQuadripoles", root.nsmap)
    for g in donneesGroupes.iterfind("./quadripole", root.nsmap):
        if g.get("nom") == element_name:
            hades_branch = g
            break

    # If element does not exist, exit program
    if hades_branch is None:
        exit("Error: Branch with the provided name does not exist")

    # Disconnect the specified branch side or both
    match BRANCH_DISCONNECTION_MODE:
        case "FROM":
            hades_branch.set("nor", "-1")
        case "TO":
            hades_branch.set("nex", "-1")
        case "BOTH":
            hades_branch.set("nex", "-1")
            hades_branch.set("nor", "-1")
        case _:
            exit("Error: Wrong disconnection mode specified")


def generate_generator_contingency(root, element_name):
    # Start by looking for the element entry
    hades_gen = None
    reseau = root.find("./reseau", root.nsmap)
    donneesGroupes = reseau.find("./donneesGroupes", root.nsmap)
    for g in donneesGroupes.iterfind("./groupe", root.nsmap):
        if g.get("nom") == element_name:
            hades_gen = g
            break

    # If element does not exist, exit program
    if hades_gen is None:
        exit("Error: Generator with the provided name does not exist")

    # Disconnect the generator
    hades_gen.set("noeud", "-1")


def generate_load_contingency(root, element_name):
    # Start by looking for the element entry
    hades_load = None
    reseau = root.find("./reseau", root.nsmap)
    donneesConsos = reseau.find("./donneesConsos", root.nsmap)
    for g in donneesConsos.iterfind("./conso", root.nsmap):
        if g.get("nom") == element_name:
            hades_load = g
            break

    # If element does not exist, exit program
    if hades_load is None:
        exit("Error: Load with the provided name does not exist")

    # Disconnect the load
    hades_load.set("noeud", "-1")


def generate_shunt_contingency(root, element_name):
    # Start by looking for the element entry
    hades_shunt = None
    reseau = root.find("./reseau", root.nsmap)
    donneesShunts = reseau.find("./donneesShunts", root.nsmap)
    for g in donneesShunts.iterfind("./shunt", root.nsmap):
        if g.get("nom") == element_name:
            hades_shunt = g
            break

    # If element does not exist, exit program
    if hades_shunt is None:
        exit("Error: Shunt with the provided name does not exist")

    # Disconnect the shunt
    hades_shunt.set("noeud", "-1")


def generate_contingency(
    hades_original_file, hades_contingency_file, contingency_element_name, contingency_element_type
):
    # Parse the hades_original_file xml with the parse_xml_file function
    # created for it, and modify the file to create the requested contingency.
    # This contingency is defined with the name of the element and a number,
    # being 1 for branch, 2 for generator, 3 for load and 4 for shunt. Save
    # the final xml file to the hades_contingency_file path.

    # Parse the hades input file
    parsed_input_xml = manage_files.parse_xml_file(hades_original_file)
    root = parsed_input_xml.getroot()

    # Add the contingency according to its type
    match contingency_element_type:
        # Branch contingency
        case 1:
            generate_branch_contingency(root, contingency_element_name)
        # Generator contingency
        case 2:
            generate_generator_contingency(root, contingency_element_name)
        # Load contingency
        case 3:
            generate_load_contingency(root, contingency_element_name)
        # Shunt contingency
        case 4:
            generate_shunt_contingency(root, contingency_element_name)
        # Default case: Not a valid element type provided
        case _:
            exit("Error: Invalid value for the contingency element type provided")

    # Save the modified xml
    etree.indent(parsed_input_xml)
    parsed_input_xml.write(
        hades_contingency_file,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="ISO-8859-1"?>',
        encoding="ISO-8859-1",
        standalone=False,
    )
