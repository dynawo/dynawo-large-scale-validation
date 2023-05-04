from lxml import etree
from dynawo_contingencies_screening.commons import manage_files
from pathlib import PurePath


BRANCH_DISCONNECTION_MODE = "BOTH"


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
    hades_original_file,
    hades_contingency_file,
    contingency_element_name,
    contingency_element_type,
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


def modify_dyd_file(
    root, ns, disconn_eventmodel, parFile_contg, cnx_id2, cnx_var2, dyd_tree, dydFile_outPath
):
    # Erase all existing Event models (keep the IDs to remove their
    # connections later below)
    old_eventIds = []
    old_parIds = []
    for event in root.iterfind(f"./{{{ns}}}blackBoxModel"):
        if event.get("lib")[0:5] == "Event":
            old_eventIds.append(event.get("id"))
            old_parIds.append(event.get("parId"))
            event.getparent().remove(event)

    # Declare a new Event
    parId = "99991234"

    event = etree.SubElement(root, f"{{{ns}}}blackBoxModel")
    event_id = "Disconnect my branch"
    event.set("id", event_id)
    event.set("lib", disconn_eventmodel)
    event.set("parFile", parFile_contg)
    event.set("parId", parId)

    # Erase all connections of the previous Events we removed above
    for cnx in root.iterfind(f"./{{{ns}}}connect"):
        if cnx.get("id1") in old_eventIds or cnx.get("id2") in old_eventIds:
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

    return parId, old_parIds


def modify_par_file(root, ns, parID, old_parIds):
    # Get the event time
    for par_set in root.iterfind("./{%s}set" % ns):
        if par_set.get("id") == parID:
            for par in par_set.iterfind("./{%s}par" % ns):
                if par.get("name") == "event_tEvent":
                    event_tEvent = float(par.get("value"))
                    break

    # Erase all existing parsets used by the Events removed above
    for parset in root.iterfind("./set", root.nsmap):
        if parset.get("id") in old_parIds:
            parset.getparent().remove(parset)

    return event_tEvent


def generate_dynawo_branch_contingency(
    dydContFile_path, dynawo_output_folder, crvFile_contg, iidm_file, element_name
):
    # Check the provided branch name exists
    iidm_file_path = dydContFile_path.parent / iidm_file
    iidm_tree = manage_files.parse_xml_file(iidm_file_path)
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    dynawo_branch = None
    for b in root.iter("{%s}line" % ns, "{%s}twoWindingsTransformer" % ns):
        if element_name == b.get("id"):
            dynawo_branch = b
            break

    # If element does not exist, exit program
    if dynawo_branch is None:
        exit("Error: Branch with the provided name does not exist")

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
    parID, old_parIds = modify_dyd_file(
        root, ns, disconn_eventmodel, parFile_contg, cnx_id2, cnx_var2, dyd_tree, dydFile_outPath
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
    event_tEvent = modify_par_file(root, ns, parID, old_parIds)

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
    if BRANCH_DISCONNECTION_MODE == "FROM":
        open_T = "false"
    if BRANCH_DISCONNECTION_MODE == "TO":
        open_F = "false"
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
    # attribute that directly provides the bus it is connected to. We
    # already stored this value in the branch_info tuple before.

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
    for b in root.iter("{%s}generator" % ns):
        if element_name == b.get("id"):
            dynawo_generator = b
            break

    # If element does not exist, exit program
    if dynawo_generator is None:
        exit("Error: Branch with the provided name does not exist")

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

    parID, old_parIds = modify_dyd_file(
        root, ns, disconn_eventmodel, parFile_contg, cnx_id2, cnx_var2, dyd_tree, dydFile_outPath
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
    event_tEvent = modify_par_file(root, ns, parID, old_parIds)

    # Insert the new parset with the params we need
    ns = etree.QName(root).namespace
    new_parset = etree.Element("{%s}set" % ns, id="99991234")
    new_parset.append(
        etree.Element("{%s}par" % ns, type="DOUBLE", name="event_tEvent", value=str(round(event_tEvent)))
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
    # attribute that directly provides the bus it is connected to. We
    # already stored this value in the Gen_info tuple before.

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


def generate_dynawo_load_contingency(dyd_tree, element_name):
    pass


def generate_dynawo_shunt_contingency(dyd_tree, element_name):
    pass


def generate_dynawo_contingency(
    dynawo_job_file, dynawo_output_folder, contingency_element_name, contingency_element_type
):
    # Parse the dynawo JOB.xml file with the parse_xml_file function
    # created for it, and extract the contingency files names from it.
    # This contingency is defined with the name of the element and a number,
    # being 1 for branch, 2 for generator, 3 for load and 4 for shunt. Save
    # the final xml file to the dynawo_output_folder path.

    # Parse the JOB file
    parsed_input_xml = manage_files.parse_xml_file(dynawo_job_file)
    root = parsed_input_xml.getroot()
    ns = etree.QName(root).namespace

    # Obtain the contingency file names
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
    match contingency_element_type:
        # Branch contingency
        case 1:
            generate_dynawo_branch_contingency(
                dydContFile_path,
                dynawo_output_folder,
                crvFile_contg,
                iidm_file,
                contingency_element_name,
            )
        # Generator contingency
        case 2:
            generate_dynawo_generator_contingency(
                dydContFile_path,
                dynawo_output_folder,
                crvFile_contg,
                iidm_file,
                contingency_element_name,
                dyd_file,
            )
        # Load contingency
        case 3:
            generate_dynawo_load_contingency(dydContFile_path, contingency_element_name)
        # Shunt contingency
        case 4:
            generate_dynawo_shunt_contingency(dydContFile_path, contingency_element_name)
        # Default case: Not a valid element type provided
        case _:
            exit("Error: Invalid value for the contingency element type provided")
