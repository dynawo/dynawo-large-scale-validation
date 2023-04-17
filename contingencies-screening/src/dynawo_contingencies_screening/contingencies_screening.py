import os
import argparse
from pathlib import Path
from dynawo_contingencies_screening.run_loadflow import run_hades
from dynawo_contingencies_screening.analyze_loadflow import extract_results_data, human_analysis

# from dynawo_contingencies_screening.run_dynawo import run_dynaflow
from dynawo_contingencies_screening.commons import manage_files


def argument_parser(command_list):
    # Define command line arguments

    p = argparse.ArgumentParser()

    if "input_dir" in command_list:
        p.add_argument(
            "input_dir",
            help="enter the path to the folder containing the case files",
        )

    if "output_dir" in command_list:
        p.add_argument(
            "output_dir",
            help="enter the path to the folder containing the case files",
        )

    if "hades_launcher" in command_list:
        p.add_argument(
            "hades_launcher",
            help="define the Hades launcher",
        )

    if "dynawo_launcher" in command_list:
        p.add_argument(
            "dynawo_launcher",
            help="define the Dynawo launcher",
        )

    if "hades_input_file" in command_list:
        p.add_argument(
            "hades_input_file",
            help="enter the path to the hades input file",
        )

    if "hades_output_file" in command_list:
        p.add_argument(
            "hades_output_file",
            help="enter the path to the hades output file",
        )

    args = p.parse_args()
    return args


def run_hades_contingencies_code(hades_input_folder, hades_output_folder, hades_launcher):

    # Find hades input file
    hades_input_file = list(hades_input_folder.glob("donneesEntreeHADES2*.xml"))[0]

    # Define hades output file
    hades_output_file = hades_output_folder / "hadesOut.xml"

    # Create output dir
    os.makedirs(hades_output_folder, exist_ok=True)

    # Run hades file (assuming all contingencies are run through the security analysis in a single run)
    run_hades.run_hades_basecase(hades_input_file, hades_output_file, hades_launcher)

    return hades_input_file, hades_output_file


def create_contingencies_ranking_code(hades_input_file, hades_output_file):

    # Parse hades xml input file
    parsed_hades_input_file = manage_files.parse_xml_file(hades_input_file)

    # Parse hades xml output file
    parsed_hades_output_file = manage_files.parse_xml_file(hades_output_file)

    # Get list of all contingencies
    contingencies_list = extract_results_data.get_contingencies_list(parsed_hades_input_file)

    # Collect Hades results in dict format
    hades_results_dict = extract_results_data.collect_hades_results(
        contingencies_list, parsed_hades_output_file
    )

    # Analyze Hades results
    loadflow_score_dict = human_analysis.analyze_loadflow_resuts(
        hades_results_dict, parsed_hades_output_file
    )

    return sorted(loadflow_score_dict.items(), key=lambda x: x[1])


def run_dynawo_contingencies_code():
    # TODO: Implement it
    pass


# From here:
# command line executables


def xml_format_dir():
    # TODO: Adapt it from prepare_basecase.py.  WARNING: Don't copy the code, call the function from the other file from this function
    pass


def run_hades_contingencies():
    # Run a hades contingency through the tool

    args = argument_parser(["input_dir", "output_dir", "hades_launcher"])

    hades_input_file, hades_output_file = run_hades_contingencies_code(
        Path(args.input_dir) / "hades", Path(args.output_dir) / "hades", args.hades_launcher
    )

    print(
        "Hades "
        + str(hades_input_file)
        + " file executed. Results file in: "
        + str(hades_output_file)
    )


def create_contingencies_ranking():
    # Create a ranking with a contingency already executed

    args = argument_parser(["hades_input_file", "hades_output_file"])

    sorted_loadflow_score_dict = create_contingencies_ranking_code(
        Path(args.hades_input_file), Path(args.hades_output_file)
    )

    print("Results ranking:")
    print(sorted_loadflow_score_dict)


def run_dynawo_contingencies():
    args = argument_parser(["input_dir", "dynawo_launcher"])

    run_dynawo_contingencies_code()


def run_contingencies_screening():
    # Main execution pipeline
    args = argument_parser(["input_dir", "output_dir", "hades_launcher"])

    hades_input_file, hades_output_file = run_hades_contingencies_code(
        Path(args.input_dir) / "hades", Path(args.output_dir) / "hades", args.hades_launcher
    )

    sorted_loadflow_score_dict = create_contingencies_ranking_code(
        hades_input_file, hades_output_file
    )

    run_dynawo_contingencies_code()
