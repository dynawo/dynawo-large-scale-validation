import os
import json
from lxml import etree
from dynawo_contingencies_screening.commons import manage_files
from pathlib import Path, PurePath
import shutil


disconnection_mode = "BOTH"
# This dictionary refers to the possible load models. Depending on each of them, the
# variable for the disconnection event can be one or another.
LOAD_MODELS = {
    "DYNModelLoadAlphaBeta": "switchOffSignal2",
    "DYNModelLoadRestorativeWithLimits": "switchOff2_value",
    "LoadAlphaBeta": "load_switchOffSignal2_value",
    "LoadAlphaBetaRestorative": "load_switchOffSignal2_value",
    "LoadAlphaBetaRestorativeLimitsRecalc": "load_switchOffSignal2_value",
    "LoadPQCompensation": "load_switchOffSignal2_value",
    "LoadPQ": "load_switchOffSignal2_value",
    "LoadZIP": "load_switchOffSignal2_value",
}


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


def create_dynawo_contingency_n_1(
    dynawo_input_folder, dynawo_output_folder, replay_cont, dict_types_cont
):
    # Contingencies (N-1)
    # Find the contingency type
    if replay_cont in dict_types_cont:
        cont_type = dict_types_cont[replay_cont]
    else:
        print("Contingency " + replay_cont + " not found in Dynawo model")
        return -1

    # Create output dir
    dynawo_output_folder = dynawo_output_folder / replay_cont
    os.makedirs(dynawo_output_folder, exist_ok=True)

    # Get the JOB.xml file path
    jobs_file = list(dynawo_input_folder.glob("*.jobs"))[0]

    # Copy all Dynawo files into the contingency subdirectory
    for file in dynawo_input_folder.iterdir():
        src_path = PurePath(dynawo_input_folder).joinpath(file.name)
        dst_path = PurePath(dynawo_output_folder).joinpath(file.name)
        if Path(file).is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            # Check if file is the symlink
            if file.name == "JOB.xml":
                Path(dst_path).symlink_to(Path(jobs_file))
            else:
                shutil.copy2(src_path, dst_path)

    # Due to the nature of Hades SA, this program does not support non-two-sided contingencies.
    disconnection_mode = "BOTH"

    # Generate contingency file
    generate_dynawo_contingency(
        dynawo_output_folder,
        dynawo_output_folder,
        replay_cont,
        cont_type,
        disconnection_mode,
    )

    return dynawo_output_folder


def modify_dyd_file(
    root,
    ns,
    disconn_eventmodel,
    parFile_contg,
    cnx_id2,
    cnx_var2,
    dyd_tree,
    dydFile_outPath,
    event_name,
):
    # Erase all existing Event models (keep the IDs to remove their
    # connections later below)
    old_event_ids = []
    old_par_ids = []
    for event in root.iterfind(f"./{{{ns}}}blackBoxModel"):
        if event.get("lib")[0:5] == "Event":
            old_event_ids.append(event.get("id"))
            old_par_ids.append(event.get("parId"))
            event.getparent().remove(event)

    # Declare a new Event
    parId = "99991234"

    event = etree.SubElement(root, f"{{{ns}}}blackBoxModel")
    event_id = event_name
    event.set("id", event_id)
    event.set("lib", disconn_eventmodel)
    event.set("parFile", parFile_contg)
    event.set("parId", parId)

    # Erase all connections of the previous Events we removed above
    for cnx in root.iterfind(f"./{{{ns}}}connect"):
        if cnx.get("id1") in old_event_ids or cnx.get("id2") in old_event_ids:
            cnx.getparent().remove(cnx)

    # Declare a new Connect between the Event model and the branch
    cnx = etree.SubElement(root, f"{{{ns}}}connect")
    cnx.set("id1", event_id)
    cnx.set("var1", "event_state1_value")
    cnx.set("id2", cnx_id2)
    cnx.set("var2", cnx_var2)

    # Write out the DYD file, preserving the XML format
    etree.indent(dyd_tree)
    dyd_tree.write(
        dydFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )

    return parId, old_par_ids


def modify_par_file(root, ns, par_id, old_par_ids):
    # Get the event time
    for par_set in root.iterfind("./{%s}set" % ns):
        if par_set.get("id") == par_id:
            for par in par_set.iterfind("./{%s}par" % ns):
                if par.get("name") == "event_tEvent":
                    event_tEvent = float(par.get("value"))
                    break

    # Erase all existing parsets used by the Events removed above
    for parset in root.iterfind("./set", root.nsmap):
        if parset.get("id") in old_par_ids:
            parset.getparent().remove(parset)

    return event_tEvent


def generate_dynawo_branch_contingency(
    dydContFile_path,
    dynawo_output_folder,
    crvFile_contg,
    iidm_file,
    element_name,
    disconnection_mode,
):
    # Check the provided branch name exists
    iidm_file_path = dydContFile_path.parent / iidm_file
    iidm_tree = manage_files.parse_xml_file(iidm_file_path)
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    dynawo_branch = None
    for b in root.iter("{%s}line" % ns, "{%s}twoWindingsTransformer" % ns):
        if element_name == b.get("id") and b.get("bus1") is not None and b.get("bus2") is not None:
            dynawo_branch = b
            break

    # If element does not exist, exit program
    if dynawo_branch is None:
        exit("Error: Branch with the provided name does not exist or is not connected to a bus")

    ###########################################################
    # DYD file: configure an event model for the disconnection
    ###########################################################

    dydFile_outPath = dynawo_output_folder / dydContFile_path.name
    dyd_tree = manage_files.parse_xml_file(dydContFile_path)
    root = dyd_tree.getroot()
    ns = etree.QName(root).namespace

    # Get the contingency par file name
    first_bbm = root.find("./{%s}blackBoxModel" % ns)
    parFile_contg = first_bbm.get("parFile")

    # Branches with vs. without a dynamic model in the DYD file:
    # they need to be disconnected differently.
    disconn_eventmodel = "EventQuadripoleDisconnection"
    cnx_id2 = "NETWORK"
    cnx_var2 = element_name + "_state_value"

    # Modify the dyd contingency file
    event_name = "Disconnect my branch"

    par_id, old_par_ids = modify_dyd_file(
        root,
        ns,
        disconn_eventmodel,
        parFile_contg,
        cnx_id2,
        cnx_var2,
        dyd_tree,
        dydFile_outPath,
        event_name,
    )

    ###########################################################
    # PAR file: add a section with the disconnection parameters
    ###########################################################

    # Get the par file tree
    parFile_outPath = dynawo_output_folder / parFile_contg
    par_file_path = dydContFile_path.parent / parFile_contg
    par_tree = manage_files.parse_xml_file(par_file_path)
    root = par_tree.getroot()
    ns = etree.QName(root).namespace

    # Modify the par contingency file
    event_tEvent = modify_par_file(root, ns, par_id, old_par_ids)

    # Insert the new parset with the params we need
    ns = etree.QName(root).namespace
    new_parset = etree.Element("{%s}set" % ns, id="99991234")
    new_parset.append(
        etree.Element(
            "{%s}par" % ns, type="DOUBLE", name="event_tEvent", value=str(round(event_tEvent))
        )
    )
    open_F = "true"
    open_T = "true"
    if disconnection_mode == "FROM":
        open_T = "false"
    elif disconnection_mode == "TO":
        open_F = "false"
    elif disconnection_mode == "BOTH":
        open_F = "false"
        open_T = "false"
    else:
        exit("Error: Wrong disconnection mode specified")

    new_parset.append(
        etree.Element("{%s}par" % ns, type="BOOL", name="event_disconnectOrigin", value=open_F)
    )
    new_parset.append(
        etree.Element("{%s}par" % ns, type="BOOL", name="event_disconnectExtremity", value=open_T)
    )
    root.append(new_parset)

    # Write out the PAR file, preserving the XML format
    etree.indent(par_tree)
    par_tree.write(
        parFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )

    ############################################################
    # CRV file: configure which variables we want in the output
    ############################################################

    # We expand the `curvesInput` section with any additional
    # variables that make sense to have in the output. The base case
    # is expected to have the variables that monitor the behavior of
    # the SVC (pilot point voltage, K level, and P,Q of participating
    # branches).  We will keep these, and add new ones.
    #
    # For now, we'll just add the voltage at the contingency bus. To do
    # this, we would use the IIDM file, where the branch has an
    # attribute that directly provides the bus it is connected to.

    branch_tag = etree.QName(dynawo_branch).localname
    if branch_tag == "line":
        branch_type = "Line"
    elif branch_tag == "twoWindingsTransformer":
        if dynawo_branch.find("{%s}phaseTapChanger" % ns) is None:
            branch_type = "Transformer"
        else:
            branch_type = "PhaseShitfer"

    # Get the buses we need to disconnect
    bus_from = get_endbus(root, dynawo_branch, branch_type, "1")
    bus_to = get_endbus(root, dynawo_branch, branch_type, "2")

    # Add the corresponding curve to the CRV file
    crvFile_outPath = dynawo_output_folder / crvFile_contg
    crv_file_path = dydContFile_path.parent / crvFile_contg
    crv_tree = manage_files.parse_xml_file(crv_file_path)
    root = crv_tree.getroot()
    ns = etree.QName(root).namespace
    new_crv1 = etree.Element("{%s}curve" % ns, model="NETWORK", variable=bus_from + "_Upu_value")
    new_crv2 = etree.Element("{%s}curve" % ns, model="NETWORK", variable=bus_to + "_Upu_value")
    root.append(new_crv1)
    root.append(new_crv2)

    # Write out the CRV file, preserving the XML format
    etree.indent(crv_tree)
    crv_tree.write(
        crvFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )


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


def generate_dynawo_generator_contingency(
    dydContFile_path, dynawo_output_folder, crvFile_contg, iidm_file, element_name, dyd_file
):
    # Check the provided generator name exists
    iidm_file_path = dydContFile_path.parent / iidm_file
    iidm_tree = manage_files.parse_xml_file(iidm_file_path)
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    dynawo_generator = None
    for g in root.iter("{%s}generator" % ns):
        if element_name == g.get("id") and g.get("bus") is not None:
            dynawo_generator = g
            break

    # If element does not exist, exit program
    if dynawo_generator is None:
        exit("Error: Generator with the provided name does not exist or is not connected to a bus")

    ###########################################################
    # DYD file: configure an event model for the disconnection
    ###########################################################

    dyd_file_path = dydContFile_path.parent / dyd_file
    dyd_tree = manage_files.parse_xml_file(dyd_file_path)
    root = dyd_tree.getroot()
    ns = etree.QName(root).namespace

    # Generators with vs. without a dynamic model in the DYD file:
    # they need to be disconnected differently.
    disconn_eventmodel = "EventConnectedStatus"
    cnx_id2 = "NETWORK"
    cnx_var2 = element_name + "_state_value"
    param_eventname = "event_open"
    for dyn_gen in root.iterfind(f"./{{{ns}}}blackBoxModel"):
        # Note we rely on dynamic model names *starting* with "Generator"
        if dyn_gen.get("lib")[0:9] == "Generator" and dyn_gen.get("staticId") == element_name:
            disconn_eventmodel = "EventSetPointBoolean"
            cnx_id2 = dyn_gen.get("id")
            cnx_var2 = "generator_switchOffSignal2_value"
            param_eventname = "event_stateEvent1"
            break

    dydFile_outPath = dynawo_output_folder / dydContFile_path.name
    dyd_tree = manage_files.parse_xml_file(dydContFile_path)
    root = dyd_tree.getroot()
    ns = etree.QName(root).namespace

    # Get the contingency par file name
    first_bbm = root.find("./{%s}blackBoxModel" % ns)
    parFile_contg = first_bbm.get("parFile")

    # Modify the dyd contingency file
    event_name = "Disconnect my gen"

    par_id, old_par_ids = modify_dyd_file(
        root,
        ns,
        disconn_eventmodel,
        parFile_contg,
        cnx_id2,
        cnx_var2,
        dyd_tree,
        dydFile_outPath,
        event_name,
    )

    ###########################################################
    # PAR file: add a section with the disconnection parameters
    ###########################################################

    # Get the par file tree
    parFile_outPath = dynawo_output_folder / parFile_contg
    par_file_path = dydContFile_path.parent / parFile_contg
    par_tree = manage_files.parse_xml_file(par_file_path)
    root = par_tree.getroot()
    ns = etree.QName(root).namespace

    # Modify the par contingency file
    event_tEvent = modify_par_file(root, ns, par_id, old_par_ids)

    # Insert the new parset with the params we need
    ns = etree.QName(root).namespace
    new_parset = etree.Element("{%s}set" % ns, id="99991234")
    new_parset.append(
        etree.Element(
            "{%s}par" % ns, type="DOUBLE", name="event_tEvent", value=str(round(event_tEvent))
        )
    )
    new_parset.append(
        etree.Element("{%s}par" % ns, type="BOOL", name=param_eventname, value="true")
    )
    root.append(new_parset)

    # Write out the PAR file, preserving the XML format
    etree.indent(par_tree)
    par_tree.write(
        parFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )

    ############################################################
    # CRV file: configure which variables we want in the output
    ############################################################

    # We expand the `curvesInput` section with any additional
    # variables that make sense to have in the output. The base case
    # is expected to have the variables that monitor the behavior of
    # the SVC (pilot point voltage, K level, and P,Q of participating
    # generators).  We will keep these, and add new ones.
    #
    # For now we'll just add the voltage at the contingency bus. To do
    # this, we would use the IIDM file, where the gen has an
    # attribute that directly provides the bus it is connected to.

    # Get the generator bus name
    topo_val = dynawo_generator.getparent().get("topologyKind")
    if topo_val == "BUS_BREAKER":
        bus_name = dynawo_generator.get("bus")
    elif topo_val == "NODE_BREAKER":
        # don't try to resolve the topology, just take the first active busbar
        bus_name = None
        vl = dynawo_generator.getparent()
        topology = vl.find("{%s}nodeBreakerTopology" % ns)
        for node in topology:
            node_type = etree.QName(node).localname
            if node_type == "busbarSection" and node.get("v") is not None:
                bus_name = node.get("id")
                break

    # Add the corresponding curve to the CRV file
    crvFile_outPath = dynawo_output_folder / crvFile_contg
    crv_file_path = dydContFile_path.parent / crvFile_contg
    crv_tree = manage_files.parse_xml_file(crv_file_path)
    root = crv_tree.getroot()
    ns = etree.QName(root).namespace
    new_crv1 = etree.Element("{%s}curve" % ns, model="NETWORK", variable=bus_name + "_Upu_value")
    root.append(new_crv1)

    # Write out the CRV file, preserving the XML format
    etree.indent(crv_tree)
    crv_tree.write(
        crvFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )


def generate_dynawo_load_contingency(
    dydContFile_path, dynawo_output_folder, crvFile_contg, iidm_file, element_name, dyd_file
):
    # Check the provided branch name exists
    iidm_file_path = dydContFile_path.parent / iidm_file
    iidm_tree = manage_files.parse_xml_file(iidm_file_path)
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    dynawo_load = None
    for load in root.iter("{%s}load" % ns):
        if element_name == load.get("id") and load.get("bus") is not None:
            dynawo_load = load
            break

    # If element does not exist, exit program
    if dynawo_load is None:
        exit("Error: Load with the provided name does not exist or is not connected to a bus")

    ###########################################################
    # DYD file: configure an event model for the disconnection
    ###########################################################

    dyd_file_path = dydContFile_path.parent / dyd_file
    dyd_tree = manage_files.parse_xml_file(dyd_file_path)
    root = dyd_tree.getroot()
    ns = etree.QName(root).namespace

    # Get the load model type
    for bbm in dyd_tree.iter("{%s}blackBoxModel" % ns):
        if bbm.get("lib") in LOAD_MODELS and bbm.get("id") == element_name:
            model_lib = bbm.get("lib")
            break

    dydFile_outPath = dynawo_output_folder / dydContFile_path.name
    dyd_tree = manage_files.parse_xml_file(dydContFile_path)
    root = dyd_tree.getroot()
    ns = etree.QName(root).namespace

    # Get the contingency par file name
    first_bbm = root.find("./{%s}blackBoxModel" % ns)
    parFile_contg = first_bbm.get("parFile")

    disconn_eventmodel = "EventSetPointBoolean"
    cnx_id2 = element_name
    cnx_var2 = model_lib
    param_eventname = "event_stateEvent1"

    # Modify the dyd contingency file
    event_name = "Disconnect my load"

    par_id, old_par_ids = modify_dyd_file(
        root,
        ns,
        disconn_eventmodel,
        parFile_contg,
        cnx_id2,
        cnx_var2,
        dyd_tree,
        dydFile_outPath,
        event_name,
    )

    ###########################################################
    # PAR file: add a section with the disconnection parameters
    ###########################################################

    # Get the par file tree
    parFile_outPath = dynawo_output_folder / parFile_contg
    par_file_path = dydContFile_path.parent / parFile_contg
    par_tree = manage_files.parse_xml_file(par_file_path)
    root = par_tree.getroot()
    ns = etree.QName(root).namespace

    # Modify the par contingency file
    event_tEvent = modify_par_file(root, ns, par_id, old_par_ids)

    # Insert the new parset with the params we need
    ns = etree.QName(root).namespace
    new_parset = etree.Element("{%s}set" % ns, id="99991234")
    new_parset.append(
        etree.Element(
            "{%s}par" % ns, type="DOUBLE", name="event_tEvent", value=str(round(event_tEvent))
        )
    )
    new_parset.append(
        etree.Element("{%s}par" % ns, type="BOOL", name=param_eventname, value="true")
    )
    root.append(new_parset)

    # Write out the PAR file, preserving the XML format
    etree.indent(par_tree)
    par_tree.write(
        parFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )

    ############################################################
    # CRV file: configure which variables we want in the output
    ############################################################

    # We expand the `curvesInput` section with any additional
    # variables that make sense to have in the output. The base case
    # is expected to have the variables that monitor the behavior of
    # the SVC (pilot point voltage, K level, and P,Q of participating
    # load).  We will keep these, and add new ones.
    #
    # For now, we'll just add the voltage at the contingency bus. To do
    # this, we would use the IIDM file, where the load has an
    # attribute that directly provides the bus it is connected to.

    # Find the bus (depends on the topology of its voltageLevel)
    topo_val = dynawo_load.getparent().get("topologyKind")
    if topo_val == "BUS_BREAKER":
        bus_name = dynawo_load.get("bus")
    elif topo_val == "NODE_BREAKER":
        # don't try to resolve the topology, just take the first active busbar
        bus_name = None
        vl = dynawo_load.getparent()
        topology = vl.find("./nodeBreakerTopology", root.nsmap)
        for node in topology:
            node_type = etree.QName(node).localname
            if node_type == "busbarSection" and node.get("v") is not None:
                bus_name = node.get("id")
                break

    # Add the corresponding curve to the CRV file
    crvFile_outPath = dynawo_output_folder / crvFile_contg
    crv_file_path = dydContFile_path.parent / crvFile_contg
    crv_tree = manage_files.parse_xml_file(crv_file_path)
    root = crv_tree.getroot()
    ns = etree.QName(root).namespace

    new_crv1 = etree.Element("{%s}curve" % ns, model="NETWORK", variable=bus_name + "_Upu_value")
    root.append(new_crv1)

    # Write out the CRV file, preserving the XML format
    etree.indent(crv_tree)
    crv_tree.write(
        crvFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )


def generate_dynawo_shunt_contingency(
    dydContFile_path, dynawo_output_folder, crvFile_contg, iidm_file, element_name
):
    # Check the provided branch name exists
    iidm_file_path = dydContFile_path.parent / iidm_file
    iidm_tree = manage_files.parse_xml_file(iidm_file_path)
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    dynawo_shunt = None
    for sh in root.iter("{%s}shunt" % ns):
        if element_name == sh.get("id") and sh.get("bus") is not None:
            dynawo_shunt = sh
            break

    # If element does not exist, exit program
    if dynawo_shunt is None:
        exit("Error: Shunt with the provided name does not exist or is not connected to a bus")

    ###########################################################
    # DYD file: configure an event model for the disconnection
    ###########################################################

    dydFile_outPath = dynawo_output_folder / dydContFile_path.name
    dyd_tree = manage_files.parse_xml_file(dydContFile_path)
    root = dyd_tree.getroot()
    ns = etree.QName(root).namespace

    # Get the contingency par file name
    first_bbm = root.find("./{%s}blackBoxModel" % ns)
    parFile_contg = first_bbm.get("parFile")

    cnx_id2 = "NETWORK"
    cnx_var2 = element_name + "_state_value"
    disconn_eventmodel = "EventConnectedStatus"
    param_eventname = "event_open"

    # Modify the dyd contingency file
    event_name = "Disconnect my shunt"

    par_id, old_par_ids = modify_dyd_file(
        root,
        ns,
        disconn_eventmodel,
        parFile_contg,
        cnx_id2,
        cnx_var2,
        dyd_tree,
        dydFile_outPath,
        event_name,
    )

    ###########################################################
    # PAR file: add a section with the disconnection parameters
    ###########################################################

    # Get the par file tree
    parFile_outPath = dynawo_output_folder / parFile_contg
    par_file_path = dydContFile_path.parent / parFile_contg
    par_tree = manage_files.parse_xml_file(par_file_path)
    root = par_tree.getroot()
    ns = etree.QName(root).namespace

    # Modify the par contingency file
    event_tEvent = modify_par_file(root, ns, par_id, old_par_ids)

    new_parset = etree.Element("{%s}set" % ns, id="99991234")
    new_parset.append(
        etree.Element(
            "{%s}par" % ns, type="DOUBLE", name="event_tEvent", value=str(round(event_tEvent))
        )
    )
    new_parset.append(
        etree.Element("{%s}par" % ns, type="BOOL", name=param_eventname, value="true")
    )
    root.append(new_parset)

    # Write out the PAR file, preserving the XML format
    etree.indent(par_tree)
    par_tree.write(
        parFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )

    ############################################################
    # CRV file: configure which variables we want in the output
    ############################################################

    # We expand the `curvesInput` section with any additional
    # variables that make sense to have in the output. The base case
    # is expected to have the variables that monitor the behavior of
    # the SVC (pilot point voltage, K level, and P,Q of participating
    # shunt).  We will keep these, and add new ones.
    #
    # For now, we'll just add the voltage at the contingency bus. To do
    # this, we would use the IIDM file, where the shunt has an
    # attribute that directly provides the bus it is connected to.

    # Get the name of the bus
    bus_name = dynawo_shunt.get("bus")

    # Add the corresponding curve to the CRV file
    crvFile_outPath = dynawo_output_folder / crvFile_contg
    crv_file_path = dydContFile_path.parent / crvFile_contg
    crv_tree = manage_files.parse_xml_file(crv_file_path)
    root = crv_tree.getroot()
    ns = etree.QName(root).namespace

    new_crv1 = etree.Element("{%s}curve" % ns, model="NETWORK", variable=bus_name + "_Upu_value")
    root.append(new_crv1)

    # Write out the CRV file, preserving the XML format
    etree.indent(crv_tree)
    crv_tree.write(
        crvFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )


def generate_dynawo_contingency(
    dynawo_input_dir,
    dynawo_output_folder,
    contingency_element_name,
    contingency_element_type,
    disconnection_mode,
):
    # Parse the dynawo JOB.xml file with the parse_xml_file function
    # created for it, and extract the contingency files names from it.
    # This contingency is defined with the name of the element and a number,
    # being 1 for branch, 2 for generator, 3 for load and 4 for shunt. Save
    # the final xml file to the dynawo_output_folder path.

    # Get the JOB file path
    dynawo_job_file = dynawo_input_dir / "JOB.xml"

    # Parse the JOB file
    parsed_input_xml = manage_files.parse_xml_file(dynawo_job_file)
    root = parsed_input_xml.getroot()
    ns = etree.QName(root).namespace

    # Obtain the needed file names
    jobs = root.findall("{%s}job" % ns)
    last_job = jobs[-1]  # contemplate only the *last* job, in case there are several
    modeler = last_job.find("{%s}modeler" % ns)
    dynModels = modeler.findall("{%s}dynModels" % ns)
    dydFile_contg = dynModels[-1].get("dydFile")
    dyd_file = dynModels[0].get("dydFile")
    outputs = last_job.find("{%s}outputs" % ns)
    curves = outputs.find("{%s}curves" % ns)
    crvFile_contg = curves.get("inputFile")
    network = modeler.find("{%s}network" % ns)
    iidm_file = network.get("iidmFile")

    dydContFile_path = PurePath(dynawo_job_file.absolute()).parent / dydFile_contg

    # Add the contingency according to its type
    if contingency_element_type == 1:
        # Branch contingency
        generate_dynawo_branch_contingency(
            dydContFile_path,
            dynawo_output_folder,
            crvFile_contg,
            iidm_file,
            contingency_element_name,
            disconnection_mode,
        )

    elif contingency_element_type == 2:
        # Generator contingency
        generate_dynawo_generator_contingency(
            dydContFile_path,
            dynawo_output_folder,
            crvFile_contg,
            iidm_file,
            contingency_element_name,
            dyd_file,
        )

    elif contingency_element_type == 3:
        # Load contingency
        generate_dynawo_load_contingency(
            dydContFile_path,
            dynawo_output_folder,
            crvFile_contg,
            iidm_file,
            contingency_element_name,
            dyd_file,
        )

    elif contingency_element_type == 4:
        # Shunt contingency
        generate_dynawo_shunt_contingency(
            dydContFile_path,
            dynawo_output_folder,
            crvFile_contg,
            iidm_file,
            contingency_element_name,
        )

    else:
        # Default case: Not a valid element type provided
        exit("Error: Invalid value for the contingency element type provided")


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

    # Check if a dynamic database is going to be used and create the needed JSON files
    if multithreading:
        n_threads = manage_files.N_THREADS_LAUNCHER
    else:
        n_threads = 1

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
