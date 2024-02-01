from lxml import etree
import os
import shutil

# Define the number of threads with which you want to configure the different execution launchers
# (eg N contingencies at the same time within a snapshot) and define the number of threads you
# want to use to execute different snapshots at the same time (eg 24 snapshots at the same time)
N_THREADS_LAUNCHER = 1

N_THREADS_SNAPSHOT = 24


def parse_xml_file(xml_file):
    # Parse the XML file to be able to process it later
    xml = xml_file
    parser = etree.XMLParser()
    parsed_xml = etree.parse(xml, parser)

    return parsed_xml


def dir_exists(input_dir, output_dir):
    # Check if exists output dir
    if output_dir.exists():
        remove_dir = input("The output directory exists " + str(output_dir) + ", do you want to remove it? [y/N] ")
        if remove_dir == "y" or remove_dir == "Y":
            # Check if output directory is the same as the input, or input
            # directory is subdirectory of the specified output directory
            if (output_dir == input_dir) or (output_dir in input_dir.parents):
                exit(
                    "Error: specified input directory is the same or a subdirectory "
                    "of the specified output directory."
                )
            else:
                shutil.rmtree(output_dir)
        else:
            exit()


def create_output_dir(
    input_dir_path, output_dir_path, time_dir, replay_dynawo, hades_folder, dynawo_folder
):
    # Create the specified output dir
    structure_path = time_dir.relative_to(input_dir_path)

    dir_exists(input_dir_path, output_dir_path / structure_path / hades_folder)
    os.makedirs(output_dir_path / structure_path / hades_folder, exist_ok=True)

    if replay_dynawo:
        dir_exists(input_dir_path, output_dir_path / structure_path / dynawo_folder)
        os.makedirs(output_dir_path / structure_path / dynawo_folder, exist_ok=True)

    return output_dir_path / structure_path


def clean_data(dynawo_output_folder, sorted_loadflow_score_list, number_pos_replay):
    # Clean all unnecessary data from Dynawo results in order to minimize the space used, always
    # keeping what is necessary for subsequent executions.
    replay_contgs = [elem_list[1]["name"] for elem_list in sorted_loadflow_score_list]
    if number_pos_replay != -1:
        replay_contgs = replay_contgs[:number_pos_replay]

    retain_files = ["aggregatedResults.xml"] + [list(dynawo_output_folder.glob("*.*iidm"))[0].name]

    retain_folders = ["outputs", "constraints", "timeLine"]
    retain_folders_contg = replay_contgs

    for elem_dir in dynawo_output_folder.iterdir():
        if elem_dir.is_file():
            if elem_dir.name not in retain_files:
                if os.path.islink(elem_dir):
                    os.unlink(elem_dir)
                else:
                    os.remove(elem_dir)
        else:
            if elem_dir.name not in retain_folders and elem_dir.name not in retain_folders_contg:
                if os.path.islink(elem_dir):
                    os.unlink(elem_dir)
                else:
                    shutil.rmtree(elem_dir)
            elif elem_dir.name in retain_folders_contg:
                for elem_contg_dir in elem_dir.iterdir():
                    if elem_contg_dir.is_file():
                        if os.path.islink(elem_contg_dir):
                            os.unlink(elem_contg_dir)
                        else:
                            os.remove(elem_contg_dir)
                    else:
                        if elem_contg_dir.name != "outputs":
                            if os.path.islink(elem_contg_dir):
                                os.unlink(elem_contg_dir)
                            else:
                                shutil.rmtree(elem_contg_dir)
                        else:
                            for output_dir in elem_contg_dir.iterdir():
                                if output_dir.is_file():
                                    if os.path.islink(output_dir):
                                        os.unlink(output_dir)
                                    else:
                                        os.remove(output_dir)
                                else:
                                    if output_dir.name != "finalState":
                                        if os.path.islink(output_dir):
                                            os.unlink(output_dir)
                                        else:
                                            shutil.rmtree(output_dir)
            elif elem_dir.name in retain_folders:
                if elem_dir.name == "outputs":
                    for elem_dir_out in elem_dir.iterdir():
                        if elem_dir_out.is_file():
                            if os.path.islink(elem_dir_out):
                                os.unlink(elem_dir_out)
                            else:
                                os.remove(elem_dir_out)
                        else:
                            if elem_dir_out.name != "finalState":
                                if os.path.islink(elem_dir_out):
                                    os.unlink(elem_dir_out)
                                else:
                                    shutil.rmtree(elem_dir_out)


def compress_results(path):
    # Compressing a folder with tar.gz, chosen for its best time-saving ratio vs xz
    os.system(
        "cd "
        + str(path.parent)
        + " && tar zcf "
        + str(path.name)
        + ".tar.gz "
        + str(path.name)
        + " && rm -rf "
        + str(path.name)
    )
