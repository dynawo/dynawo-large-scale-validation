from lxml import etree
import os

N_THREADS_LAUNCHER = 8

N_THREADS_SNAPSHOT = 8


def parse_xml_file(xml_file):
    # Parse the XML file to be able to process it later
    xml = xml_file
    parser = etree.XMLParser()
    parsed_xml = etree.parse(xml, parser)

    return parsed_xml


def create_output_dir(
    input_dir_path, output_dir_path, time_dir, replay_dynawo, hades_folder, dynawo_folder
):
    # Create the specified output dir
    structure_path = time_dir.relative_to(input_dir_path)
    os.makedirs(output_dir_path / structure_path / hades_folder, exist_ok=True)

    if replay_dynawo:
        os.makedirs(output_dir_path / structure_path / dynawo_folder, exist_ok=True)

    return output_dir_path / structure_path
