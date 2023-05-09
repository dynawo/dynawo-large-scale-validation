import os
from lxml import etree
from dynawo_contingencies_screening.commons import manage_files


def generate_branch_contingency(root, element_name, disconnection_mode):
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
    match disconnection_mode:
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


def clean_contingencies(parsed_input_xml, root, ns):
    # Clear contingencies from previous runs and from the original run with
    # the goal of running only the target contingency
    for variante in root.iter("{%s}variante" % ns):
        variante.getparent().remove(variante)


def generate_contingency(
    hades_original_file_parsed,
    hades_contingency_file,
    contingency_element_name,
    contingency_element_type,
    disconnection_mode,
):
    # Parse the hades_original_file xml with the parse_xml_file function
    # created for it, and modify the file to create the requested contingency.
    # This contingency is defined with the name of the element and a number,
    # being 1 for branch, 2 for generator, 3 for load and 4 for shunt. Save
    # the final xml file to the hades_contingency_file path.

    root = hades_original_file_parsed.getroot()
    # Add the contingency according to its type
    match contingency_element_type:
        # Branch contingency
        case 1:
            generate_branch_contingency(root, contingency_element_name, disconnection_mode)
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
    etree.indent(hades_original_file_parsed)
    hades_original_file_parsed.write(
        hades_contingency_file,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="ISO-8859-1"?>',
        encoding="ISO-8859-1",
        standalone=False,
    )


def get_types_cont(hades_input_file):
    parsed_hades = manage_files.parse_xml_file(hades_input_file)
    root = parsed_hades.getroot()
    ns = etree.QName(root).namespace

    # Get all the types of the different elements
    dict_types_cont = {}
    for entry in root.iter("{%s}quadripole" % ns):
        dict_types_cont[entry.attrib["nom"]] = 1

    for entry in root.iter("{%s}groupe" % ns):
        dict_types_cont[entry.attrib["nom"]] = 2

    for entry in root.iter("{%s}conso" % ns):
        dict_types_cont[entry.attrib["nom"]] = 3

    for entry in root.iter("{%s}shunt" % ns):
        dict_types_cont[entry.attrib["nom"]] = 4

    return dict_types_cont


def create_hades_contingency_n_1(
    hades_input_file, hades_input_file_parsed, hades_output_folder, replay_cont, dict_types_cont
):
    # Contingencies (N-1)

    # Find the contingency type
    if replay_cont in dict_types_cont:
        cont_type = dict_types_cont[replay_cont]
    else:
        exit("Contingency type not found")

    # Create output dir
    os.makedirs(hades_output_folder / replay_cont, exist_ok=True)

    # TODO: Get the disconnection mode from input file
    disconnection_mode = "BOTH"

    # Generate contingency file
    generate_contingency(
        hades_input_file_parsed,
        hades_output_folder / replay_cont / hades_input_file.name,
        replay_cont,
        cont_type,
        disconnection_mode,
    )

    return hades_output_folder / replay_cont
