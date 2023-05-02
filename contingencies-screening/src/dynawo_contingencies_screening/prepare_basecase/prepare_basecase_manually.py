from pathlib import Path, PurePath
from lxml import etree
import shutil
import subprocess


def xml_format_dir(input_dir):
    subprocess.run(
        [str(PurePath(Path(__file__).absolute()).parent / "xml_format_dir.sh"), str(input_dir)]
    )


def create_basecase_directory(input_dir, output_dir):
    # Copy the formatted directory onto the new basecase directory
    # xml_format_dir.sh adds .FORMATTED suffix in the input directory name
    formatted_directory = Path(str(input_dir) + ".FORMATTED")
    shutil.copytree(formatted_directory, output_dir)

    # Create the dynawo subdirectory
    dynawo_directory = Path(output_dir / "dynawo")

    if not dynawo_directory.exists():
        dynawo_directory.mkdir()

    # In case the JOB.xml file does not already exist, create it
    jobs_file = list(formatted_directory.glob("*.jobs"))[0]

    if not (output_dir / "JOB.xml").exists():
        dest_file = output_dir / "JOB.xml"
        dest_file.symlink_to(Path(jobs_file))

    # Move all Dynawo files into the dynawo subdirectory
    for file in output_dir.iterdir():
        if file.name != "Hades" and file.name != "hades" and file.name != "dynawo":
            src_path = PurePath(output_dir).joinpath(file.name)
            dst_path = PurePath(dynawo_directory).joinpath(file.name)
            # Check if file is the symlink
            if file.name == "JOB.xml":
                Path(dst_path).symlink_to(Path(jobs_file))
                Path(src_path).unlink()
            else:
                shutil.move(src_path, dst_path)
        # Check if hades folder needs to be renamed
        if file.name == "Hades":
            file.rename(PurePath(file.absolute()).parent / "hades")

    return dynawo_directory


def modify_stop_time(root, ns):
    # Find the simulation stopTime value and double it
    for simulation_data in root.iter("{%s}simulation" % ns):
        t_event = int(simulation_data.attrib["stopTime"])  # Save value for the .par file
        new_stop_time = t_event * 2
        simulation_data.attrib["stopTime"] = str(new_stop_time)

    return t_event


def enable_constraints(root, ns):
    # Search and enable the constraints file
    for branch in root.iter("{%s}outputs" % ns):
        # If tag does not exist, create it
        if branch.find("{%s}constraints" % ns) is None:
            new_constraint = etree.SubElement(branch, "{%s}constraints" % ns)
            new_constraint.set("exportMode", "XML")
        else:
            for constraints_data in branch.iter("{%s}constraints" % ns):
                constraints_data.attrib["exportMode"] = "XML"


def enable_timeline(root, ns):
    # Search and enable the timeline file
    for branch in root.iter("{%s}outputs" % ns):
        # If tag does not exist, create it
        if branch.find("{%s}timeline" % ns) is None:
            new_timeline = etree.SubElement(branch, "{%s}timeline" % ns)
            new_timeline.set("exportMode", "XML")
        else:
            for timeline_data in branch.iter("{%s}timeline" % ns):
                timeline_data.attrib["exportMode"] = "XML"


def enable_curves(root, ns):
    # Search and enable the curves file
    for branch in root.iter("{%s}outputs" % ns):
        # If tag does not exist, create it
        if branch.find("{%s}curves" % ns) is None:
            new_curves = etree.SubElement(branch, "{%s}curves" % ns)
            # NOTE: Values must be changed depending on the case
            new_curves.set("inputFile", "standard_curves.crv")
            new_curves.set("exportMode", "CSV")
        else:
            for data_curves in branch.iter("{%s}curves" % ns):
                # NOTE: Values must be changed depending on the case
                data_curves.attrib["inputFile"] = "standard_curves.crv"
                data_curves.attrib["exportMode"] = "XML"


def enable_pf_output(root, ns):
    # Search and enable the PF output
    for branch in root.iter("{%s}outputs" % ns):
        # If tag does not exist, create it
        if branch.find("{%s}finalState" % ns) is None:
            new_pf = etree.SubElement(branch, "{%s}finalState" % ns)
            new_pf.set("exportIIDMFile", "true")
            new_pf.set("exportDumpFile", "false")
        else:
            for pf_data in branch.iter("{%s}finalState" % ns):
                pf_data.attrib["exportIIDMFile"] = "true"
                pf_data.attrib["exportDumpFile"] = "false"


def save_xml_changes(job_tree, destination_path, encoding, standalone=True):
    # Indent the tree, then add the xml header and save it.
    etree.indent(job_tree)

    if not standalone:
        job_tree.write(
            destination_path,
            xml_declaration=True,
            encoding=encoding,
            standalone=False,
            pretty_print=True,
        )
    else:
        job_tree.write(
            destination_path,
            xml_declaration=True,
            encoding=encoding,
            pretty_print=True,
        )


def format_job_file(basecase_path):
    # Start by reading the JOB.xml file
    job_file = str(basecase_path) + "/JOB.xml"

    # Convert the JOB.xml file to an ElementTree object
    job_tree = etree.parse(job_file)
    xml_root = job_tree.getroot()
    ns = etree.QName(xml_root).namespace

    # Modify the JOB.xml file and save it
    t_event = modify_stop_time(xml_root, ns)
    enable_constraints(xml_root, ns)
    enable_curves(xml_root, ns)
    enable_timeline(xml_root, ns)
    enable_pf_output(xml_root, ns)
    save_xml_changes(job_tree, job_file, "ISO-8859-1", standalone=False)

    return t_event


def run_add_contg_job(job_file_path):
    # Runs the "add_contig_job.py" code to add the new .dyd file
    tree = etree.parse(str(job_file_path), etree.XMLParser(remove_blank_text=True))
    root = tree.getroot()
    ns = etree.QName(root).namespace

    for dyd_file in root.iter(f"{{{ns}}}dynModels"):
        dir_dyd_file = dyd_file.get("dydFile")
        dir_dyd = PurePath(dir_dyd_file).parent
        if len(str(dir_dyd)) != 0:
            dir_dyd = dir_dyd / ""
        dir_dyd_contg = dir_dyd / "contingency.dyd"
        event = etree.SubElement(dyd_file.getparent(), f"{{{ns}}}dynModels")
        event.set("dydFile", dir_dyd_contg)

    find = False
    for crv_file in root.iter(f"{{{ns}}}curves"):
        find = True

    if not find:
        for output in root.iter(f"{{{ns}}}outputs"):
            event = etree.SubElement(output, f"{{{ns}}}curves")
            event.set("exportMode", "CSV")
            event.set("inputFile", "standard_curves.crv")

    save_xml_changes(tree, job_file_path, "UTF-8")


def create_dyd_file(file_path, data_dyd):
    # Start by creating the main tag of
    # the .dyd file and registering the namespace
    ns = "http://www.rte-france.com/dynawo"
    etree.register_namespace("dyn", ns)
    dyd_tree = etree.Element("{%s}dynamicModelsArchitecture" % ns)

    # Create the blackBoxModel tag with its attributes
    par_id = 99991234  # Par ID value to be used in the .par file creation
    blackbox_tag = etree.SubElement(dyd_tree, "{%s}blackBoxModel" % ns)
    blackbox_tag.set("id", "Disconnect my branch")
    blackbox_tag.set("lib", "EventQuadripoleDisconnection")
    blackbox_tag.set("parFile", "contingency.par")
    blackbox_tag.set("parId", str(par_id))

    # Create the connect tag with its attributes
    connect_tag = etree.SubElement(dyd_tree, "{%s}connect" % ns)
    connect_tag.set("id1", "Disconnect my branch")
    connect_tag.set("var1", "event_state1_value")
    connect_tag.set("id2", "NETWORK")
    # NOTE: Values must be changed depending on the case
    connect_tag.set("var2", data_dyd)

    # Save the new xml onto the .dyd file
    out_tree = etree.ElementTree(dyd_tree)
    destination_path = file_path / "contingency.dyd"
    save_xml_changes(out_tree, destination_path, "UTF-8", standalone=False)

    return par_id


def create_par_file(file_path, t_event, id_par):
    # Start by creating the main tag of
    # the .par file and registering the namespace
    ns = "http://www.rte-france.com/dynawo"
    par_tree = etree.Element("parametersSet")
    par_tree.set("xmlns", ns)

    # Create the set tag
    set_tag = etree.SubElement(par_tree, "set")
    set_tag.set("id", str(id_par))

    # Create the par events
    n_par_events = 3
    for i in range(n_par_events):
        par_tag = etree.SubElement(set_tag, "par")
        match i:
            case 0:
                par_tag.set("name", "event_tEvent")
                par_tag.set("type", "DOUBLE")
                par_tag.set("value", str(t_event))

            case 1:
                par_tag.set("name", "event_disconnectOrigin")
                par_tag.set("type", "BOOL")
                par_tag.set("value", "true")

            case 2:
                par_tag.set("name", "event_disconnectExtremity")
                par_tag.set("type", "BOOL")
                par_tag.set("value", "true")

    # Save the new xml into the .par file
    out_tree = etree.ElementTree(par_tree)
    destination_path = file_path / "contingency.par"
    save_xml_changes(out_tree, destination_path, "UTF-8", standalone=False)


def create_curves_file(file_path, data_curves):
    # Start by creating the main tag of
    # the .crv file and registering the namespace
    ns = "http://www.rte-france.com/dynawo"
    crv_tree = etree.Element("curvesInput")
    crv_tree.set("xmlns", ns)

    # Create the first comment line
    crv_tree.append(
        etree.Comment(" === Pilot bus and gens associated " "to S.V.C. zone: RST_BARNAP7 === ")
    )

    # Create the curve variables
    for value_pair in data_curves:
        crv_tag = etree.SubElement(crv_tree, "curve")
        crv_tag.set("model", value_pair[0])
        crv_tag.set("variable", value_pair[1])

    # Create the last comment line
    crv_tree.append(etree.Comment(" === below, the contingency-specific curves === "))

    # Save the new xml into the .crv file
    out_tree = etree.ElementTree(crv_tree)
    destination_path = file_path / "standard_curves.crv"
    save_xml_changes(out_tree, destination_path, "UTF-8")


def run_prepare_pipeline(input_dir, output_dir):
    # Main pipeline of events
    xml_format_dir(input_dir)
    basecase_path = create_basecase_directory(input_dir, output_dir)
    event_time = format_job_file(basecase_path)
    run_add_contg_job((basecase_path / "JOB.xml"))

    # TODO: Modify this
    # Note: create_dyd_file and create_curves_file functions are using
    # arbitrary ID data values during the file creation, in future versions
    # these values should be obtained depending on the contingency to evaluate.
    dyd_data = ".ABAN 7 .GUEN 1_state_value"
    par_id = create_dyd_file(basecase_path, dyd_data)
    create_par_file(basecase_path, event_time, par_id)
    curves_data = [
        ("NETWORK", "BARNAP71_Upu_value"),
        ("PALUE7PALUET2", "generator_PGenPu"),
        ("PALUE7PALUET2", "generator_QGenPu"),
        ("PALUE7PALUET4", "generator_PGenPu"),
        ("PALUE7PALUET4", "generator_QGenPu"),
    ]
    create_curves_file(basecase_path, curves_data)
