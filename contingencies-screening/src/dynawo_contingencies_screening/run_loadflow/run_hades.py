import shutil
import subprocess
from lxml import etree
from dynawo_contingencies_screening.commons import manage_files


def activate_tap_changers(hades_file, activate_taps, multithreading):
    # Modify the input file in order to activate the tap changers
    if activate_taps:
        activate_taps_str = "true"
    else:
        activate_taps_str = "false"

    hades_tree = manage_files.parse_xml_file(hades_file)
    root = hades_tree.getroot()
    ns = etree.QName(root).namespace

    for paramHades in root.iter("{%s}paramHades" % ns):
        paramHades.set("regChrg", activate_taps_str)
        if not multithreading:
            paramHades.set("nbThreads", "1")

    hades_tree.write(
        hades_file,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=False,
        pretty_print=True,
    )


def run_hades(hades_input_file, hades_output_file, hades_launcher, tap_changers, multithreading):
    # Get the output folder (using hades_output_file parent folder) to be able to
    # copy the input file into the outputs folder, and with this last file (copy of
    # the input located in the output folder), run hades through Python with the
    # launcher provided in the arguments, leaving the result in the hades_output_file

    # We obtain the output folder path
    # and copy the input file there
    output_folder = hades_output_file.parent
    if output_folder != hades_input_file.parent:
        shutil.copy(hades_input_file, output_folder)

    # Activate tap changers if needed
    activate_tap_changers(output_folder / hades_input_file.name, tap_changers, multithreading)

    # Run the simulation on the specified hades launcher
    subprocess.run(
        "cd "
        + str(output_folder)
        + " && "
        + str(hades_launcher)
        + " "
        + str(output_folder / hades_input_file.name)
        + " "
        + str(hades_output_file),
        shell=True,
        check=True,
    )
