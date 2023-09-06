import os
import json
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
    if disconnection_mode == "FROM":
        hades_branch.set("nor", "-1")
    elif disconnection_mode == "TO":
        hades_branch.set("nex", "-1")
    elif disconnection_mode == "BOTH":
        hades_branch.set("nex", "-1")
        hades_branch.set("nor", "-1")
    else:
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
    if contingency_element_type == 1:
        # Branch contingency
        generate_branch_contingency(root, contingency_element_name, disconnection_mode)
    elif contingency_element_type == 2:
        # Generator contingency
        generate_generator_contingency(root, contingency_element_name)
    elif contingency_element_type == 3:
        # Load contingency
        generate_load_contingency(root, contingency_element_name)
    elif contingency_element_type == 4:
        # Shunt contingency
        generate_shunt_contingency(root, contingency_element_name)
    else:
        # Default case: Not a valid element type provided
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
    # Get a dictionary with the different types of Hades contingencies
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
    # Create the Hades contingencies one by one, in order to get the full loadflows
    # Contingencies (N-1)

    # Find the contingency type
    if replay_cont in dict_types_cont:
        cont_type = dict_types_cont[replay_cont]
    else:
        print("Contingency " + replay_cont + " not found in Hades model")
        return -1

    # Create output dir
    os.makedirs(hades_output_folder / replay_cont, exist_ok=True)

    # Due to the nature of Hades SA, this program does not support non-two-sided contingencies.
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


def get_dynawo_types_cont(dynawo_input_file):
    # Get a dictionary with the different types of Dynawo contingencies
    parsed_iidm = manage_files.parse_xml_file(dynawo_input_file)
    root = parsed_iidm.getroot()
    ns = etree.QName(root).namespace

    # Get all the types of the different elements
    dict_types_cont = {}
    for entry in root.iter("{%s}line" % ns, "{%s}twoWindingsTransformer" % ns):
        if entry.get("bus1") is not None and entry.get("bus2") is not None:
            dict_types_cont[entry.attrib["id"]] = 1

    for entry in root.iter("{%s}generator" % ns):
        if entry.get("bus") is not None:
            dict_types_cont[entry.attrib["id"]] = 2

    for entry in root.iter("{%s}load" % ns):
        if entry.get("bus") is not None:
            dict_types_cont[entry.attrib["id"]] = 3

    for entry in root.iter("{%s}shunt" % ns):
        if entry.get("bus") is not None:
            dict_types_cont[entry.attrib["id"]] = 4

    return dict_types_cont


def get_endbus(root, branch, branch_type, side):
    ns = etree.QName(root).namespace
    end_bus = branch.get("bus" + side)
    if end_bus is None:
        end_bus = branch.get("connectableBus" + side)
    if end_bus is None:
        # bummer, the bus is NODE_BREAKER
        topo = []
        #  for xfmers, we only need to search the VLs within the substation
        if branch_type == "Line":
            pnode = root
        else:
            pnode = branch.getparent()
        for vl in pnode.iter("{%s}voltageLevel" % ns):
            if vl.get("id") == branch.get("voltageLevelId" + side):
                topo = vl.find("{%s}nodeBreakerTopology" % ns)
                break
        # we won't resolve the actual topo connectivity; just take the first busbar
        for node in topo:
            node_type = etree.QName(node).localname
            if node_type == "busbarSection" and node.get("v") is not None:
                end_bus = node.get("id")
                break
    return end_bus


def create_dynawo_SA(
    dynawo_output_folder,
    replay_contgs,
    dict_types_cont,
    dynamic_database,
    matched_branches,
    matched_generators,
    matched_loads,
    matched_shunts,
    multithreading,
):
    # Create all the necessary files to be able to carry out the Dynawo SA, taking advantage of
    # the opportunities offered by dynaflow-launcher, without having to manually create the
    # contingencies one by one.

    # Set up the number of execution threads
    if multithreading:
        n_threads = manage_files.N_THREADS_LAUNCHER
    else:
        n_threads = 1

    # Check if a dynamic database is going to be used and create the needed JSON files
    if dynamic_database is not None:
        setting_xml = list(dynamic_database.glob("*setting*.xml"))[0]
        assembling_xml = list(dynamic_database.glob("*assembling*.xml"))[0]

        config_dict = {
            "dfl-config": {
                "OutputDir": str(dynawo_output_folder),
                "SettingPath": str(setting_xml),
                "AssemblingPath": str(assembling_xml),
                "ChosenOutputs": ["STEADYSTATE", "LOSTEQ", "TIMELINE", "CONSTRAINTS"],
                "sa": {
                    "NumberOfThreads": n_threads,
                },
            }
        }
        contng_dict = {
            "version": "1.0",
            "name": "list",
            "contingencies": [],
        }
    else:
        config_dict = {
            "dfl-config": {
                "OutputDir": str(dynawo_output_folder),
                "ChosenOutputs": ["STEADYSTATE", "LOSTEQ", "TIMELINE", "CONSTRAINTS"],
                "sa": {
                    "NumberOfThreads": n_threads,
                },
            }
        }
        contng_dict = {
            "version": "1.0",
            "name": "list",
            "contingencies": [],
        }

    # Create output dir
    os.makedirs(dynawo_output_folder, exist_ok=True)

    # Replay the contingencies
    for replay_cont in replay_contgs:
        if dict_types_cont[replay_cont] == 1:
            if replay_cont not in matched_branches.keys():
                print("Contingency " + replay_cont + " not matched in Dynawo.")
                continue
            else:
                if matched_branches[replay_cont] == "Line":
                    type_cont = "LINE"
                elif matched_branches[replay_cont] in ["Transformer", "PhaseShitfer"]:
                    type_cont = "TWO_WINDINGS_TRANSFORMER"
        elif dict_types_cont[replay_cont] == 2:
            type_cont = "GENERATOR"
            if replay_cont not in matched_generators:
                print("Contingency " + replay_cont + " not matched in Dynawo.")
                continue
        elif dict_types_cont[replay_cont] == 3:
            type_cont = "LOAD"
            if replay_cont not in matched_loads:
                print("Contingency " + replay_cont + " not matched in Dynawo.")
                continue
        elif dict_types_cont[replay_cont] == 4:
            type_cont = "SHUNT_COMPENSATOR"
            if replay_cont not in matched_shunts:
                print("Contingency " + replay_cont + " not matched in Dynawo.")
                continue
        else:
            continue

        contng_dict["contingencies"].append(
            {"id": replay_cont, "elements": [{"id": replay_cont, "type": type_cont}]}
        )

    # Save the JSON files
    with open(dynawo_output_folder / "config.json", "w") as outfile:
        json.dump(config_dict, outfile, indent=2)

    with open(dynawo_output_folder / "contng.json", "w") as outfile:
        json.dump(contng_dict, outfile, indent=2)

    return dynawo_output_folder / "config.json", dynawo_output_folder / "contng.json", contng_dict
