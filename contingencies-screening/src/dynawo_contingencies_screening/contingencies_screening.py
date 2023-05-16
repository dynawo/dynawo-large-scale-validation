import os
import shutil
import copy
import argparse
import pandas as pd
from pathlib import Path
from lxml import etree
from dynawo_contingencies_screening.run_loadflow import run_hades
from dynawo_contingencies_screening.analyze_loadflow import (
    extract_results_data,
    human_analysis,
    machine_learning_analysis,
)
from dynawo_contingencies_screening.prepare_basecase import prepare_basecase, create_contingencies, matching_elements
from dynawo_contingencies_screening.run_dynawo import run_dynawo
from dynawo_contingencies_screening.commons import manage_files


HADES_FOLDER = "hades"
DYNAWO_FOLDER = "dynawo"
REPLAY_NUM = 25
DEFAULT_SCORE = 1


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

    if "hades_original_file" in command_list:
        p.add_argument(
            "hades_original_file",
            help="enter the path to the hades original file",
        )

    if "hades_contingency_file" in command_list:
        p.add_argument(
            "hades_contingency_file",
            help="enter the path to the hades contingency file",
        )

    if "contingency_element_name" in command_list:
        p.add_argument(
            "contingency_element_name",
            help="enter the name of the contingency element",
        )

    if "contingency_element_type" in command_list:
        p.add_argument(
            "contingency_element_type",
            help="enter the type of the contingency element",
            type=int,
        )

    if "tap_changers" in command_list:
        p.add_argument(
            "-t",
            "--tap_changers",
            help="run the simulations with activated tap changers",
            action="store_true",
        )

    if "replay_hades" in command_list:
        p.add_argument(
            "-a",
            "--replay_hades",
            help="replay the worst contingencies with Hades",
            action="store_true",
        )

    if "replay_dynawo" in command_list:
        p.add_argument(
            "-d",
            "--replay_dynawo",
            help="replay the worst contingencies with Dynawo",
            action="store_true",
        )

    if "branch_disconnection_mode" in command_list:
        p.add_argument(
            "-b",
            "--branch_disconnection_mode",
            help="define the branch_disconnection_mode (FROM, TO, BOTH)",
            default="BOTH",
        )

    if "n_replay" in command_list:
        p.add_argument(
            "-n",
            "--n_replay",
            help="define the number of worst contingencies to replay (FROM, TO, BOTH)",
            type=int,
            default=REPLAY_NUM,
        )

    if "score_type" in command_list:
        p.add_argument(
            "-s",
            "--score_type",
            help="Define the type of scoring used in the ranking (1 = discrete human made, 2 = continuous human made, 3 = machine learning disc, 4 = machine learning cont",
            type=int,
            default=DEFAULT_SCORE,
        )

    if "dynawo_job_file" in command_list:
        p.add_argument(
            "dynawo_job_file",
            help="enter the path to the dynawo job file",
        )

    args = p.parse_args()
    return args


def dir_exists(input_dir, output_dir):
    # Check if exists output dir
    if output_dir.exists():
        remove_dir = input("The output directory exists, do you want to remove it? [y/N] ")
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


def solve_launcher(launcher):
    # Check if it is a file in the system path or a directory to a file
    if launcher.is_file():
        launcher_solved = launcher.absolute()
    else:
        launcher_solved = launcher

    return launcher_solved


def run_hades_contingencies_code(
    hades_input_folder, hades_output_folder, hades_launcher, tap_changers
):
    # Find hades input file
    hades_input_file = list(hades_input_folder.glob("donneesEntreeHADES2*.xml"))[0]

    # Define hades output file
    hades_output_file = hades_output_folder / "hadesOut.xml"

    # Create output dir
    os.makedirs(hades_output_folder, exist_ok=True)

    # Run hades file (assuming all contingencies are run through the security analysis in a single run)
    run_hades.run_hades(hades_input_file, hades_output_file, hades_launcher, tap_changers)

    return hades_input_file, hades_output_file


def sort_ranking(elem):
    lambda x: x[1]["final_score"]
    if type(elem[1]["final_score"]) == str:
        if elem[1]["final_score"] == "Divergence":
            return 999999999
        else:
            return 0
    else:
        return elem[1]["final_score"]


def create_contingencies_ranking_code(
    hades_input_file, hades_output_file, score_type, tap_changers
):
    # Parse hades xml input file
    parsed_hades_input_file = manage_files.parse_xml_file(hades_input_file)

    # Parse hades xml output file
    parsed_hades_output_file = manage_files.parse_xml_file(hades_output_file)

    # Get dict of all contingencies
    hades_elements_dict = extract_results_data.get_elements_dict(parsed_hades_input_file)

    # Get dict of all contingencies
    hades_contingencies_dict = extract_results_data.get_contingencies_dict(parsed_hades_input_file)

    # Collect Hades results in dict format
    hades_elements_dict, hades_contingencies_dict = extract_results_data.collect_hades_results(
        hades_elements_dict, hades_contingencies_dict, parsed_hades_output_file
    )

    # Analyze Hades results
    match score_type:
        case 1:
            hades_contingencies_dict = human_analysis.analyze_loadflow_results_discrete(
                hades_contingencies_dict, hades_elements_dict
            )

            # Used to temporarily store dataframes, in order to use them for ML
            # df_temp, error_contg = machine_learning_analysis.convert_dict_to_df(
            #     hades_contingencies_dict, hades_elements_dict, True, True
            # )

            # if (Path(os.getcwd()) / "disc_df.csv").is_file():
            #     df_ant = pd.read_csv(Path(os.getcwd()) / "disc_df.csv", sep=";", index_col="NUM")
            #     df_temp = pd.concat([df_ant, df_temp], ignore_index=False)

            # df_temp.to_csv(Path(os.getcwd()) / "disc_df.csv", sep=";")
        case 2:
            hades_contingencies_dict = human_analysis.analyze_loadflow_results_continuous(
                hades_contingencies_dict, hades_elements_dict
            )

            # Used to temporarily store dataframes, in order to use them for ML
            # df_temp, error_contg = machine_learning_analysis.convert_dict_to_df(
            #     hades_contingencies_dict, hades_elements_dict, False, True
            # )

            # if (Path(os.getcwd()) / "cont_df.csv").is_file():
            #     df_ant = pd.read_csv(Path(os.getcwd()) / "cont_df.csv", sep=";", index_col="NUM")
            #     df_temp = pd.concat([df_ant, df_temp], ignore_index=False)

            # df_temp.to_csv(Path(os.getcwd()) / "cont_df.csv", sep=";")
        case 3:
            hades_contingencies_dict = machine_learning_analysis.analyze_loadflow_results(
                hades_contingencies_dict, hades_elements_dict, True, tap_changers
            )
        case 4:
            hades_contingencies_dict = machine_learning_analysis.analyze_loadflow_results(
                hades_contingencies_dict, hades_elements_dict, False, tap_changers
            )
        case _:
            exit("There is no defined score for the indicated option")

    return sorted(hades_contingencies_dict.items(), key=sort_ranking, reverse=True)


def prepare_hades_contingencies(
    sorted_loadflow_score_dict, hades_input_file, hades_output_folder, number_pos_replay
):
    # Create the worst contingencies manually in order to replay it with Hades launcher
    replay_contgs = [
        [elem_list[1]["name"], elem_list[1]["type"]] for elem_list in sorted_loadflow_score_dict
    ]
    replay_contgs = replay_contgs[:number_pos_replay]

    hades_output_list = []

    dict_types_cont = create_contingencies.get_types_cont(hades_input_file)

    # Parse the hades input file and clean contingencies
    hades_input_file_parsed = manage_files.parse_xml_file(hades_input_file)
    root = hades_input_file_parsed.getroot()
    create_contingencies.clean_contingencies(
        hades_input_file_parsed, root, etree.QName(root).namespace
    )

    for replay_cont in replay_contgs:
        if replay_cont[1] == 0:
            hades_input_file_parsed_copy = copy.deepcopy(hades_input_file_parsed)
            # Contingencies (N-1)
            # Generate the fist N(number_pos_replay) contingencies
            hades_output_file = create_contingencies.create_hades_contingency_n_1(
                hades_input_file,
                hades_input_file_parsed_copy,
                hades_output_folder,
                replay_cont[0],
                dict_types_cont,
            )

            if hades_output_file != -1:
                hades_output_list.append(hades_output_file)
        else:
            # TODO: Implement other types of contingencies (ex. N-k)
            continue

    return hades_output_list


def prepare_dynawo_contingencies(
    sorted_loadflow_score_dict, dynawo_input_folder, dynawo_output_folder, number_pos_replay
):
    # Create the worst contingencies manually in order to replay it with Hades launcher
    replay_contgs = [
        [elem_list[1]["name"], elem_list[1]["type"]] for elem_list in sorted_loadflow_score_dict
    ]
    replay_contgs = replay_contgs[:number_pos_replay]

    dynawo_output_list = []

    # Get the JOB file path
    dynawo_job_file = dynawo_input_folder / "JOB.xml"

    # Parse the JOB file
    parsed_input_xml = manage_files.parse_xml_file(dynawo_job_file)
    root = parsed_input_xml.getroot()
    ns = etree.QName(root).namespace

    # Get the .iidm filename
    jobs = root.findall("{%s}job" % ns)
    last_job = jobs[-1]  # contemplate only the *last* job, in case there are several
    modeler = last_job.find("{%s}modeler" % ns)
    network = modeler.find("{%s}network" % ns)
    iidm_file = network.get("iidmFile")

    dict_types_cont = create_contingencies.get_dynawo_types_cont(dynawo_input_folder / iidm_file)

    for replay_cont in replay_contgs:
        if replay_cont[1] == 0:
            # Contingencies (N-1)
            # Generate the fist N(number_pos_replay) contingencies
            dynawo_output_file = create_contingencies.create_dynawo_contingency_n_1(
                dynawo_input_folder,
                dynawo_output_folder,
                replay_cont[0],
                dict_types_cont,
            )

            if dynawo_output_file != -1:
                dynawo_output_list.append(dynawo_output_file)
        else:
            # TODO: Implement other types of contingencies (ex. N-k)
            continue

    return dynawo_output_list


def run_dynawo_contingencies_code(input_dir, output_dir, dynawo_launcher):
    # TODO: Implement it

    # Create output dir
    os.makedirs(output_dir, exist_ok=True)

    # Run the BASECASE with the specified Dynawo launcher
    run_dynawo.run_dynaflow(input_dir, output_dir, dynawo_launcher)


def display_results_table(output_dir, sorted_loadflow_score_dict):
    str_table = "{:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14}\n".format(
        "POS",
        "NUM",
        "NAME",
        "AFFECTED_ELEM",
        "STATUS",
        "MIN_VOLT",
        "MAX_VOLT",
        "N_ITER",
        "CONSTR_GEN_Q",
        "CONSTR_GEN_U",
        "CONSTR_VOLT",
        "CONSTR_FLOW",
        "FINAL_SCORE",
    )

    i_count = 0
    for elem_list in sorted_loadflow_score_dict:
        i_count += 1
        str_table += "{:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14} {:<14}\n".format(
            i_count,
            elem_list[0],
            elem_list[1]["name"],
            str(len(elem_list[1]["affected_elements"])),
            str(elem_list[1]["status"]),
            str(len(elem_list[1]["min_voltages"])),
            str(len(elem_list[1]["max_voltages"])),
            str(elem_list[1]["n_iter"]),
            str(len(elem_list[1]["constr_gen_Q"])),
            str(len(elem_list[1]["constr_gen_U"])),
            str(len(elem_list[1]["constr_volt"])),
            str(len(elem_list[1]["constr_flow"])),
            elem_list[1]["final_score"],
        )

    print(str_table)

    text_file = open(output_dir / "results_table.txt", "w")
    n = text_file.write(str_table)
    text_file.close()


# From here:
# command line executables


def check_basecase_dir(input_dir):
    # Run the BASECASE directory check
    prepare_basecase.check_basecase_dir(Path(input_dir).absolute())


def run_hades_contingencies():
    # Run a hades contingency through the tool

    args = argument_parser(["input_dir", "output_dir", "hades_launcher", "tap_changers"])

    dir_exists(Path(args.input_dir).absolute(), Path(args.output_dir).absolute())

    hades_launcher_solved = solve_launcher(Path(args.hades_launcher))

    hades_input_file, hades_output_file = run_hades_contingencies_code(
        Path(args.input_dir).absolute() / HADES_FOLDER,
        Path(args.output_dir).absolute() / HADES_FOLDER,
        hades_launcher_solved,
        args.tap_changers,
    )

    print(
        "Hades "
        + str(hades_input_file)
        + " file executed. Results file in: "
        + str(hades_output_file)
    )


def create_contingencies_ranking():
    # Create a ranking with a contingency already executed

    args = argument_parser(["hades_input_file", "hades_output_file", "score_type", "tap_changers"])

    sorted_loadflow_score_dict = create_contingencies_ranking_code(
        Path(args.hades_input_file).absolute(),
        Path(args.hades_output_file).absolute(),
        args.score_type,
        args.tap_changers,
    )

    print("Results ranking:")
    print(sorted_loadflow_score_dict)


def run_dynawo_contingencies():
    # Run a dynawo contingency through the tool

    args = argument_parser(["input_dir", "output_dir", "dynawo_launcher"])

    dynawo_launcher_solved = solve_launcher(Path(args.dynawo_launcher))

    run_dynawo_contingencies_code(
        Path(args.input_dir).absolute() / DYNAWO_FOLDER,
        Path(args.output_dir).absolute() / DYNAWO_FOLDER,
        dynawo_launcher_solved,
    )


def create_dynawo_contingency():
    # Create a single dynawo contingency

    args = argument_parser(
        [
            "input_dir",
            "output_dir",
            "contingency_element_name",
            "contingency_element_type",
        ]
    )

    create_contingencies.generate_dynawo_contingency(
        Path(args.input_dir).absolute() / DYNAWO_FOLDER,
        Path(args.output_dir).absolute() / DYNAWO_FOLDER,
        args.contingency_element_name,
        args.contingency_element_type,
    )


def extract_matching_elements():
    args = argument_parser(
        [
            "hades_input_file",
            "dynawo_job_file",
        ]
    )

    (
        matched_branches,
        matched_generators,
        matched_loads,
        matched_shunts,
    ) = matching_elements.matching_elements(
        Path(args.hades_input_file).absolute(), Path(args.dynawo_job_file).absolute()
    )


def run_contingencies_screening():
    # Main execution pipeline
    args = argument_parser(
        [
            "input_dir",
            "output_dir",
            "hades_launcher",
            "dynawo_launcher",
            "tap_changers",
            "replay_hades",
            "replay_dynawo",
            "n_replay",
            "score_type",
        ]
    )

    dir_exists(Path(args.input_dir).absolute(), Path(args.output_dir).absolute())

    prepare_basecase.check_basecase_dir(Path(args.input_dir).absolute())

    hades_launcher_solved = solve_launcher(Path(args.hades_launcher))
    dynawo_launcher_solved = solve_launcher(Path(args.dynawo_launcher))

    hades_input_file, hades_output_file = run_hades_contingencies_code(
        Path(args.input_dir).absolute() / HADES_FOLDER,
        Path(args.output_dir).absolute() / HADES_FOLDER,
        hades_launcher_solved,
        args.tap_changers,
    )

    sorted_loadflow_score_dict = create_contingencies_ranking_code(
        hades_input_file,
        hades_output_file,
        args.score_type,
        args.tap_changers,
    )

    display_results_table(Path(args.output_dir), sorted_loadflow_score_dict)

    if args.replay_hades:
        replay_hades_paths = prepare_hades_contingencies(
            sorted_loadflow_score_dict, hades_input_file, hades_output_file.parent, args.n_replay
        )

        for replay_hades_path in replay_hades_paths:
            hades_input_file, hades_output_file = run_hades_contingencies_code(
                replay_hades_path,
                replay_hades_path,
                hades_launcher_solved,
                args.tap_changers,
            )

    if args.replay_dynawo:
        dynawo_input_dir = Path(args.input_dir).absolute() / DYNAWO_FOLDER
        dynawo_output_dir = Path(args.output_dir).absolute() / DYNAWO_FOLDER

        replay_dynawo_paths = prepare_dynawo_contingencies(
            sorted_loadflow_score_dict, dynawo_input_dir, dynawo_output_dir, args.n_replay
        )

        for replay_dynawo_path in replay_dynawo_paths:
            run_dynawo_contingencies_code(
                replay_dynawo_path,
                replay_dynawo_path,
                dynawo_launcher_solved,
            )
