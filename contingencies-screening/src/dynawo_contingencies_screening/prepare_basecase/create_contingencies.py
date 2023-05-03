from lxml import etree
from dynawo_contingencies_screening.commons import manage_files
from pathlib import PurePath


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


def generate_dynawo_branch_contingency(dydFile_path, dynawo_output_folder, element_name):
    ###########################################################
    # DYD file: configure an event model for the disconnection
    ###########################################################

    dydFile_outPath = dynawo_output_folder / dydFile_path
    dyd_tree = manage_files.parse_xml_file(dydFile_path)
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
    dyd_tree.write(
        dydFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8"
    )

    ###########################################################
    # PAR file: add a section with the disconnection parameters
    ###########################################################

    # Get the par file tree
    parFile_outPath = dynawo_output_folder / parFile_contg
    par_file_path = dydFile_path.parent / parFile_contg
    par_tree = manage_files.parse_xml_file(par_file_path)
    root = par_tree.getroot()
    ns = etree.QName(root).namespace

    # Erase all existing parsets used by the Events removed above
    for parset in root.iterfind("./set", root.nsmap):
        if parset.get("id") in old_parIds:
            parset.getparent().remove(parset)

    # Get the event time
    for par_set in root.iterfind("./{%s}set" % ns):
        if par_set.get("id") == parId:
            for par in par_set.iterfind("./{%s}par" % ns):
                if par.get("name") == "event_tEvent":
                    event_tEvent = float(par.get("value"))
                    break

    # Insert the new parset with the params we need
    ns = etree.QName(root).namespace
    new_parset = etree.Element("{%s}set" % ns, id="99991234")
    new_parset.append(
        etree.Element("{%s}par" % ns, type="DOUBLE", name="event_tEvent", value=event_tEvent)
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
    par_tree.write(
        parFile_outPath,
        pretty_print=True,
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
        encoding="UTF-8",
    )

    ############################################################
    # CRV file: configure which variables we want in the output
    ############################################################
    # TODO: Finish the function and check its functionality


def generate_dynawo_generator_contingency(dyd_tree, element_name):
    pass


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
    dydFile_path = PurePath(dynawo_job_file.absolute()).parent / dydFile_contg

    # Add the contingency according to its type
    match contingency_element_type:
        # Branch contingency
        case 1:
            generate_dynawo_branch_contingency(dydFile_path, dynawo_output_folder, contingency_element_name)
        # Generator contingency
        case 2:
            generate_dynawo_generator_contingency(dydFile_path, contingency_element_name)
        # Load contingency
        case 3:
            generate_dynawo_load_contingency(dydFile_path, contingency_element_name)
        # Shunt contingency
        case 4:
            generate_dynawo_shunt_contingency(dydFile_path, contingency_element_name)
        # Default case: Not a valid element type provided
        case _:
            exit("Error: Invalid value for the contingency element type provided")
