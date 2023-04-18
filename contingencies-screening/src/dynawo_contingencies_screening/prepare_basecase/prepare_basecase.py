import os
import argparse
from pathlib import Path
from lxml import etree


def parser(args_type):
    p = argparse.ArgumentParser()
    if args_type == 1:
        p.add_argument(
            "case_dir",
            help="enter the path to the folder containing the case files",
        )

    args = p.parse_args()
    return args


def xml_format_dir():
    args = parser(1)

    os.system(
        str(Path(os.path.dirname(os.path.abspath(__file__))))
        + "/xml_format_dir.sh "
        + str(Path(args.case_dir))
    )


def create_basecase_directory():
    args = parser(1)

    # Copy the formatted directory onto the new basecase directory
    data_path = str(Path(os.path.dirname(os.path.abspath(__file__))))
    separator = "."
    formatted_directory = (
        data_path + "/"
        + str(args.case_dir).split(separator)[0]
        + ".ORIG.FORMATTED"
    )
    basecase_directory = (
        data_path + "/" + str(args.case_dir).split(separator)[0] + ".BASECASE"
    )
    os.system("cp -a " + formatted_directory + " " + basecase_directory)

    # In case the JOB.xml file does not already exist, create it
    if not os.path.exists(basecase_directory + "/JOB.xml"):
        os.system(
            "ln -s "
            + formatted_directory
            + "/*.jobs "
            + basecase_directory
            + "/JOB.xml"
        )

    return basecase_directory


def modify_stop_time(root, ns):
    # Find the simulation stopTime value and double it
    for simulation_data in root.iter("{%s}simulation" % ns):
        t_event = int(
            simulation_data.attrib["stopTime"]
        )  # Save value for the .par file
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
            # NOTE: Values must be changed deepending on the case
            new_curves.set("inputFile", "standard_curves.crv")
            new_curves.set("exportMode", "CSV")
        else:
            for curves_data in branch.iter("{%s}curves" % ns):
                # NOTE: Values must be changed deepending on the case
                curves_data.attrib["inputFile"] = "standard_curves.crv"
                curves_data.attrib["exportMode"] = "XML"


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


def save_xml_changes(job_tree, destination_path):
    # Indent the tree, then add the xml header and save it.
    etree.indent(job_tree)
    job_tree.write(
        destination_path,
        xml_declaration=True,
        encoding="ISO-8859-1",
        standalone=False,
        pretty_print=True,
    )


def format_job_file():
    args = parser(1)

    # Start by reading the JOB.xml file
    data_path = str(Path(os.path.dirname(os.path.abspath(__file__))))
    separator = "."
    job_file = (
        data_path + "/"
        + str(args.case_dir).split(separator)[0]
        + ".BASECASE/JOB.xml"
    )

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
    save_xml_changes(job_tree, job_file)

    return t_event


def run_add_contg_job(job_file_path):
    # Runs the "add_contig_job.py" script to add the neu .dyd file
    os.system("python3 add_contg_job.py " + job_file_path + "/JOB.xml")


def create_dyd_file(file_path):
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
    # NOTE: Values must be changed deepending on the case
    connect_tag.set("var2", ".ABAN 7 .GUEN 1_state_value")

    # Save the new xml onto the .dyd file
    out_tree = etree.ElementTree(dyd_tree)
    etree.indent(out_tree)
    out_tree.write(
        file_path + "/contingency.dyd",
        xml_declaration=True,
        encoding="UTF-8",
        standalone=False,
        pretty_print=True,
    )

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
    etree.indent(out_tree)
    out_tree.write(
        file_path + "/contingency.par",
        xml_declaration=True,
        encoding="UTF-8",
        standalone=False,
        pretty_print=True,
    )


def create_curves_file(file_path):
    # Start by creating the main tag of
    # the .crv file and registering the namespace
    ns = "http://www.rte-france.com/dynawo"
    crv_tree = etree.Element("curvesInput")
    crv_tree.set("xmlns", ns)

    # Create the first comment line
    crv_tree.append(
        etree.Comment(
            " === Pilot bus and gens associated "
            "to S.V.C. zone: RST_BARNAP7 === "
        )
    )

    # Create the curve variables
    # NOTE: Values must be changed deepending on the case
    n_curves = 4
    for i in range(n_curves + 1):  # We add the NETWORK line as well
        crv_tag = etree.SubElement(crv_tree, "curve")
        match i:
            case 0:
                crv_tag.set("model", "NETWORK")
                crv_tag.set("variable", "BARNAP71_Upu_value")

            case 1:
                crv_tag.set("model", "PALUE7PALUET2")
                crv_tag.set("variable", "generator_PGenPu")

            case 2:
                crv_tag.set("model", "PALUE7PALUET2")
                crv_tag.set("variable", "generator_QGenPu")

            case 3:
                crv_tag.set("model", "PALUE7PALUET4")
                crv_tag.set("variable", "generator_PGenPu")

            case 4:
                crv_tag.set("model", "PALUE7PALUET4")
                crv_tag.set("variable", "generator_QGenPu")

    # Create the last comment line
    crv_tree.append(
        etree.Comment(" === below, the contingency-specific curves === ")
    )

    # Save the new xml into the .crv file
    out_tree = etree.ElementTree(crv_tree)
    etree.indent(out_tree)
    out_tree.write(
        file_path + "/standard_curves.crv",
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )


if __name__ == "__main__":
    # Main pipeline of events
    xml_format_dir()
    basecase_path = create_basecase_directory()
    event_time = format_job_file()
    run_add_contg_job(basecase_path)
    par_id = create_dyd_file(basecase_path)
    create_par_file(basecase_path, event_time, par_id)
    create_curves_file(basecase_path)