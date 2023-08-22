import os
import shutil
import subprocess
from dynawo_contingencies_screening.commons import manage_files
from lxml import etree


def run_dynaflow(input_dir, output_dir, dynawo_launcher):
    # From the data specified in the input directory,
    # run the simulation with the desired Dynawo launcher

    # We obtain the output folder path
    # and copy the input file there
    for fname in input_dir.glob("**/*"):
        shutil.copy2(input_dir / fname, output_dir)

    # Run the simulation on the specified dynawo launcher
    subprocess.run(
        str(dynawo_launcher) + " jobs " + str(output_dir) + "/JOB.xml ",
        shell=True,
        check=True,
    )


def check_calculated_contg(input_dir, matching_contng_dict):
    # Check if a contingency is in the files of contingencies already executed, in order to know if it
    # can be reused or not (eg contingencies executed 1,2,3,4. 2 and 4 are wanted, therefore it can be
    # reused. If 2,4,5 were needed, it would not be possible)

    parsed_file = manage_files.parse_xml_file(input_dir / "aggregatedResults.xml")

    set_dict = set()
    for i in matching_contng_dict["contingencies"]:
        set_dict.add(i["id"])

    set_xml = set()
    root = parsed_file.getroot()
    ns = etree.QName(root).namespace
    for contg in root.iter("{%s}scenarioResults" % ns):
        set_xml.add(contg.attrib["id"])

    return not set_dict.issubset(set_xml)


def run_dynaflow_SA(
    input_dir,
    output_dir,
    dynawo_launcher,
    config_file,
    contng_file,
    calc_contingencies,
    matching_contng_dict,
):
    # From the data specified in the input directory, run the simulation in the desired Dynawo
    # launcher or reuse the data provided.

    replay_dynawo = True
    if calc_contingencies:
        replay_dynawo = check_calculated_contg(input_dir, matching_contng_dict)
        if not replay_dynawo:
            os.system(
                "find "
                + str(input_dir)
                + " -mindepth 1 -maxdepth 1 -exec ln -sf '{}' "
                + str(output_dir)
                + "/ \;"
            )

    if replay_dynawo:
        iidm_file = list(input_dir.glob("*.*iidm"))[0]
        # We obtain the output folder path
        # and copy the input file there
        shutil.copy2(iidm_file, output_dir)

        # Run the simulation on the specified dynawo launcher
        try:
            subprocess.run(
                str(dynawo_launcher)
                + " launch --network "
                + str(output_dir / iidm_file.name)
                + " --config "
                + str(config_file)
                + " --contingencies "
                + str(contng_file)
                + " --nsa",
                shell=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return 1

    return 0
