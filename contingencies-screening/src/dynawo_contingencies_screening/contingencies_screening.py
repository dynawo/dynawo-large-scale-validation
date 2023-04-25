import os
import shutil
import argparse
import pandas as pd
from pathlib import Path
from dynawo_contingencies_screening.run_loadflow import run_hades
from dynawo_contingencies_screening.analyze_loadflow import extract_results_data, human_analysis
from dynawo_contingencies_screening.prepare_basecase import prepare_basecase
from dynawo_contingencies_screening.run_dynawo import run_dynawo
from dynawo_contingencies_screening.commons import manage_files

HADES_FOLDER = "hades"
DYNAWO_FOLDER = "dynawo"


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


def dir_exists(dir_path):
    # Check if exists output dir
    if dir_path.exists():
        remove_dir = input("The output directory exists, do you want to remove it? [y/N] ")
        if remove_dir == "y" or remove_dir == "Y":
            shutil.rmtree(dir_path)
        else:
            exit()


def solve_launcher(launcher):
    # Check if it is a file in the system path or a directory to a file
    if launcher.is_file():
        launcher_solved = launcher.absolute()
    else:
        launcher_solved = launcher

    return launcher_solved


def run_hades_contingencies_code(hades_input_folder, hades_output_folder, hades_launcher):

    # Find hades input file
    hades_input_file = list(hades_input_folder.glob("donneesEntreeHADES2*.xml"))[0]

    # Define hades output file
    hades_output_file = hades_output_folder / "hadesOut.xml"

    # Create output dir
    os.makedirs(hades_output_folder, exist_ok=True)

    # Run hades file (assuming all contingencies are run through the security analysis in a single run)
    run_hades.run_hades(hades_input_file, hades_output_file, hades_launcher)

    return hades_input_file, hades_output_file


def create_contingencies_ranking_code(hades_input_file, hades_output_file):

    # Parse hades xml input file
    parsed_hades_input_file = manage_files.parse_xml_file(hades_input_file)

    # Parse hades xml output file
    parsed_hades_output_file = manage_files.parse_xml_file(hades_output_file)

    # Get list of all contingencies
    hades_contingencies_dict = extract_results_data.get_contingencies_dict(parsed_hades_input_file)

    # Collect Hades results in dict format
    hades_contingencies_dict = extract_results_data.collect_hades_results(
        hades_contingencies_dict, parsed_hades_output_file
    )

    # Analyze Hades results
    hades_contingencies_dict = human_analysis.analyze_loadflow_resuts(
        hades_contingencies_dict, parsed_hades_output_file
    )

    return sorted(
        hades_contingencies_dict.items(), key=lambda x: x[1]["final_score"], reverse=True
    )


def run_dynawo_contingencies_code(input_dir, output_dir, dynawo_launcher):
    # TODO: Implement it

    # Create output dir
    os.makedirs(output_dir, exist_ok=True)

    # Run the BASECASE with the specified Dynawo launcher
    run_dynawo.run_dynaflow(input_dir, output_dir, dynawo_launcher)


def display_results_table(output_dir, sorted_loadflow_score_list):

    str_table = "{:<15} {:<15} {:<15} {:<15}\n".format("NUM", "NOM", "DATA", "FINAL_SCORE")
    for elem_list in sorted_loadflow_score_list:
        str_table += "{:<15} {:<15} {:<15} {:<15}\n".format(
            elem_list[0],
            elem_list[1]["nom"],
            elem_list[1]["temp_data"],
            elem_list[1]["final_score"],
        )

    print(str_table)

    text_file = open(output_dir / "results_table.txt", "w")
    n = text_file.write(str_table)
    text_file.close()


# From here:
# command line executables


def prepare_basecase_dir():
    # Run the BASECASE preparation pipeline
    args = argument_parser(["input_dir", "output_dir"])

    prepare_basecase.run_prepare_pipeline(
        Path(args.input_dir).absolute(), Path(args.output_dir).absolute()
    )


def run_hades_contingencies():
    # Run a hades contingency through the tool

    args = argument_parser(["input_dir", "output_dir", "hades_launcher"])

    dir_exists(Path(args.output_dir).absolute())

    hades_launcher_solved = solve_launcher(Path(args.hades_launcher))

    hades_input_file, hades_output_file = run_hades_contingencies_code(
        Path(args.input_dir).absolute() / HADES_FOLDER,
        Path(args.output_dir).absolute() / HADES_FOLDER,
        hades_launcher_solved,
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
        Path(args.hades_input_file).absolute(), Path(args.hades_output_file).absolute()
    )

    print("Results ranking:")
    print(sorted_loadflow_score_dict)


def run_dynawo_contingencies():
    args = argument_parser(["input_dir", "output_dir", "dynawo_launcher"])

    dynawo_launcher_solved = solve_launcher(Path(args.dynawo_launcher))

    run_dynawo_contingencies_code(
        Path(args.input_dir).absolute() / DYNAWO_FOLDER,
        Path(args.output_dir).absolute() / DYNAWO_FOLDER,
        dynawo_launcher_solved,
    )


def run_contingencies_screening():
    # Main execution pipeline
    args = argument_parser(["input_dir", "output_dir", "hades_launcher", "dynawo_launcher"])

    dir_exists(Path(args.output_dir).absolute())

    hades_launcher_solved = solve_launcher(Path(args.hades_launcher))
    dynawo_launcher_solved = solve_launcher(Path(args.dynawo_launcher))

    hades_input_file, hades_output_file = run_hades_contingencies_code(
        Path(args.input_dir).absolute() / HADES_FOLDER,
        Path(args.output_dir).absolute() / HADES_FOLDER,
        hades_launcher_solved,
    )

    sorted_loadflow_score_dict = create_contingencies_ranking_code(
        hades_input_file, hades_output_file
    )

    display_results_table(Path(args.output_dir), sorted_loadflow_score_dict)

    run_dynawo_contingencies_code(
        Path(args.input_dir).absolute() / DYNAWO_FOLDER,
        Path(args.output_dir).absolute() / DYNAWO_FOLDER,
        dynawo_launcher_solved,
    )
