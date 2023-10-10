import os
import shutil
import copy
import argparse
import multiprocessing
import pandas as pd
from pathlib import Path
from lxml import etree
from dynawo_contingencies_screening.run_loadflow import run_hades
from dynawo_contingencies_screening.analyze_loadflow import (
    extract_results_data,
    human_analysis,
    machine_learning_analysis,
)
from dynawo_contingencies_screening.prepare_basecase import (
    create_contingencies,
    matching_elements,
)
from dynawo_contingencies_screening.run_dynawo import run_dynawo
from dynawo_contingencies_screening.commons import (
    manage_files,
    calc_case_diffs,
)

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
            help="enter the path to the output folder",
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

    if "tap_changers" in command_list:
        p.add_argument(
            "-t",
            "--tap_changers",
            help="run the simulations with activated tap changers",
            action="store_true",
        )

    if "replay_hades_obo" in command_list:
        p.add_argument(
            "-a",
            "--replay_hades_obo",
            help="replay the most interesting contingencies with Hades one by one",
            action="store_true",
        )

    if "replay_dynawo" in command_list:
        p.add_argument(
            "-d",
            "--replay_dynawo",
            help="replay the most interesting contingencies with Dynawo",
            action="store_true",
        )

    if "n_replay" in command_list:
        p.add_argument(
            "-n",
            "--n_replay",
            help="define the number of most interesting contingencies to replay (default = "
            + str(REPLAY_NUM)
            + ")",
            type=int,
            default=REPLAY_NUM,
        )

    if "score_type" in command_list:
        p.add_argument(
            "-s",
            "--score_type",
            help="define the type of scoring used in the ranking (1 = human made, "
            "2 = machine learning)",
            type=int,
            default=DEFAULT_SCORE,
        )

    if "dynamic_database" in command_list:
        p.add_argument(
            "-b",
            "--dynamic_database",
            help="path to use a standalone dynamic database when running Dynawo",
            default=None,
        )

    if "multithreading" in command_list:
        p.add_argument(
            "-m",
            "--multithreading",
            help="enable multithreading executions in Hades",
            action="store_true",
        )

    if "calc_contingencies" in command_list:
        p.add_argument(
            "-c",
            "--calc_contingencies",
            help="the input files have the contingencies calculated previously",
            action="store_true",
        )

    if "compress_results" in command_list:
        p.add_argument(
            "-z",
            "--compress_results",
            help="clean and compress the results",
            action="store_true",
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
    hades_input_folder,
    hades_output_folder,
    hades_launcher,
    tap_changers,
    multithreading,
    calc_contingencies,
):
    # Find hades input file
    hades_input_list = list(hades_input_folder.glob("donneesEntreeHADES2*.xml"))

    # Check if the file exists
    if len(hades_input_list) == 0:
        print("Hades input file not found")
        return "", "", 1
    else:
        hades_input_file = hades_input_list[0]

    # Define hades output file
    hades_output_file = hades_output_folder / "hadesOut.xml"

    # Run hades file (assuming all contingencies are run through the security analysis
    # in a single run)
    status = run_hades.run_hades(
        hades_input_file,
        hades_output_file,
        hades_launcher,
        tap_changers,
        multithreading,
        calc_contingencies,
    )

    return hades_input_file, hades_output_file, status


def sort_ranking(elem):
    # Criterion to define and order the ranking of contingencies
    if type(elem[1]["final_score"]) == str:
        return 0
    else:
        return elem[1]["final_score"]


def create_contingencies_ranking_code(
    hades_input_file, hades_output_file, output_dir_path, score_type, tap_changers
):
    # Parse hades xml input file
    parsed_hades_input_file = manage_files.parse_xml_file(hades_input_file)

    # Parse hades xml output file
    parsed_hades_output_file = manage_files.parse_xml_file(hades_output_file)

    # Get dict of all elements
    hades_elements_dict = extract_results_data.get_elements_dict(parsed_hades_input_file)

    # Get dict of all contingencies
    hades_contingencies_dict = extract_results_data.get_contingencies_dict(parsed_hades_input_file)

    # Collect Hades results in dict format
    (
        hades_elements_dict,
        hades_contingencies_dict,
        status,
    ) = extract_results_data.collect_hades_results(
        hades_elements_dict, hades_contingencies_dict, parsed_hades_output_file, tap_changers
    )

    # Check if the results of the contingencies have been found within the output of hades
    if status == 1:
        return hades_contingencies_dict, 1

    # Analyze the results of hades based on the type of scoring that has been chosen, be it
    # human analysis (LR) or AI
    if score_type == 1:
        hades_contingencies_dict = human_analysis.analyze_loadflow_results_continuous(
            hades_contingencies_dict, hades_elements_dict, tap_changers
        )
    elif score_type == 2:
        hades_contingencies_dict = machine_learning_analysis.analyze_loadflow_results(
            hades_contingencies_dict, hades_elements_dict, tap_changers
        )
    else:
        exit("There is no defined score for the indicated option")

    # Used to store dataframes, in order to use them for ML or results analysis
    df_temp, error_contg = machine_learning_analysis.convert_dict_to_df(
        hades_contingencies_dict,
        hades_elements_dict,
        tap_changers,
        True,
    )

    # Save the DF as a csv file
    df_temp.to_csv(output_dir_path / "contg_df.csv", sep=";")

    return sorted(hades_contingencies_dict.items(), key=sort_ranking, reverse=True), 0


def prepare_hades_contingencies(
    sorted_loadflow_score_list, hades_input_file, hades_output_folder, number_pos_replay
):
    # Create the worst contingencies manually in order to replay it with Hades launcher
    replay_contgs = [
        [elem_list[1]["name"], elem_list[1]["type"]] for elem_list in sorted_loadflow_score_list
    ]

    # If the number -1 has been provided, all contingencies will be replayed
    if number_pos_replay != -1:
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
            print(
                "Due to the nature of Hades SA, this program does not "
                "support non-N-1 contingencies. How for example, N - k."
            )

    return hades_output_list


def prepare_dynawo_SA(
    hades_input_file,
    sorted_loadflow_score_list,
    dynawo_input_folder,
    dynawo_output_folder,
    number_pos_replay,
    dynamic_database,
    multithreading,
):
    # Create the worst contingencies with JSON in order to replay it with Dynaflow launcher
    replay_contgs = [elem_list[1]["name"] for elem_list in sorted_loadflow_score_list]

    # If the number -1 has been provided, all contingencies will be replayed
    if number_pos_replay != -1:
        replay_contgs = replay_contgs[:number_pos_replay]

    iidm_list = list(dynawo_input_folder.glob("*.*iidm"))

    # Check if the file exists
    if len(iidm_list) == 0:
        print("Dynawo input file not found")
        return "", "", "", 1
    else:
        iidm_file = iidm_list[0]

    # Match elements between Hades and Dynawo
    (
        matched_branches,
        matched_generators,
        matched_loads,
        matched_shunts,
    ) = matching_elements.matching_elements(hades_input_file, iidm_file)

    dict_types_cont = create_contingencies.get_dynawo_types_cont(dynawo_input_folder / iidm_file)

    # Contingencies (N-1)
    # Generate the fist N(number_pos_replay) contingencies
    config_file, contng_file, contng_dict = create_contingencies.create_dynawo_SA(
        dynawo_output_folder,
        replay_contgs,
        dict_types_cont,
        dynamic_database,
        matched_branches,
        matched_generators,
        matched_loads,
        matched_shunts,
        multithreading,
    )

    return config_file, contng_file, contng_dict, 0


def run_dynawo_contingencies_SA_code(
    input_dir,
    output_dir,
    dynawo_launcher,
    config_file,
    contng_file,
    calc_contingencies,
    matching_contng_dict,
):
    # Create output dir
    os.makedirs(output_dir, exist_ok=True)

    # Run the BASECASE with the specified Dynawo launcher
    status = run_dynawo.run_dynaflow_SA(
        input_dir,
        output_dir,
        dynawo_launcher,
        config_file,
        contng_file,
        calc_contingencies,
        matching_contng_dict,
    )

    return status


def extract_dynawo_results(dynawo_output_folder, sorted_loadflow_score_list, number_pos_replay):
    # Parse the results of the contingencies
    dynawo_output_file = dynawo_output_folder / "outputs" / "finalState" / "outputIIDM.xml"
    parsed_output_file = manage_files.parse_xml_file(dynawo_output_file)
    dynawo_aggregated_xml = dynawo_output_folder / "aggregatedResults.xml"
    parsed_aggregated_file = manage_files.parse_xml_file(dynawo_aggregated_xml)

    replay_contgs = [elem_list[1]["name"] for elem_list in sorted_loadflow_score_list]
    # If the number -1 has been provided, all contingencies will be replayed
    if number_pos_replay != -1:
        replay_contgs = replay_contgs[:number_pos_replay]

    contg_set = set(replay_contgs)

    # Collect the dynawo contingencies data
    dynawo_contingency_data, dynawo_tap_data = extract_results_data.collect_dynawo_results(
        parsed_output_file, parsed_aggregated_file, dynawo_output_folder, contg_set
    )

    return dynawo_contingency_data


def calculate_case_differences(
    sorted_loadflow_score_list, dynawo_contingency_data, matching_contingencies_dict
):
    # Calculate the differences for each of the contingencies executed in both loadflows
    dict_diffs = {}
    for case in matching_contingencies_dict["contingencies"]:
        hades_key = calc_case_diffs.get_hades_id(case["id"], sorted_loadflow_score_list)

        if case["id"] in dynawo_contingency_data:
            dict_diffs[case["id"]] = calc_case_diffs.calculate_diffs_hades_dynawo(
                sorted_loadflow_score_list[hades_key], dynawo_contingency_data[case["id"]]
            )
        else:
            print("WARNING: Case " + case["id"] + " not executed by Dynaflow.")

    return pd.DataFrame.from_dict(
        dict_diffs, orient="index", columns=["NAME", "STATUS", "REAL_SCORE"]
    )


def display_results_table(output_dir, sorted_loadflow_score_list, tap_changers):
    # Display the results table through the console depending on whether tap changers
    # have been used or not
    if tap_changers:
        str_table = (
            "{:<7} {:<7} {:<14} {:<14} {:<7} {:<10} {:<10} {:<10} {:<13} "
            "{:<13} {:<13} {:<13} {:<12} {:<10} {:<14} {:<14}\n".format(
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
                "COEF_REPORT",
                "RES_NODE",
                "TAP_CHANGERS",
                "FINAL_SCORE",
            )
        )

        i_count = 0
        for elem_list in sorted_loadflow_score_list:
            i_count += 1
            str_table += (
                "{:<7} {:<7} {:<14} {:<14} {:<7} {:<10} {:<10} {:<10} {:<13} {:<13} "
                "{:<13} {:<13} {:<12} {:<10} {:<14} {:<14}\n".format(
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
                    str(len(elem_list[1]["coef_report"])),
                    str(len(elem_list[1]["res_node"])),
                    str(len(elem_list[1]["tap_changers"])),
                    elem_list[1]["final_score"],
                )
            )
    else:
        str_table = (
            "{:<7} {:<7} {:<14} {:<14} {:<7} {:<10} {:<10} {:<10} {:<13} "
            "{:<13} {:<13} {:<13} {:<12} {:<10} {:<14}\n".format(
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
                "COEF_REPORT",
                "RES_NODE",
                "FINAL_SCORE",
            )
        )

        i_count = 0
        for elem_list in sorted_loadflow_score_list:
            i_count += 1
            str_table += (
                "{:<7} {:<7} {:<14} {:<14} {:<7} {:<10} {:<10} {:<10} {:<13} {:<13} "
                "{:<13} {:<13} {:<12} {:<10} {:<14}\n".format(
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
                    str(len(elem_list[1]["coef_report"])),
                    str(len(elem_list[1]["res_node"])),
                    elem_list[1]["final_score"],
                )
            )

    print(str_table)

    # Save the results table in a txt
    text_file = open(output_dir / "results_table.txt", "w")
    text_file.write(str_table)
    text_file.close()


def run_contingencies_screening_thread_loop(
    args, time_dir, input_dir_path, output_dir_path, hades_launcher_solved, dynawo_launcher_solved
):
    # Main function for each of the snapshots, which carries out the entire process of execution,
    # analysis and comparison

    if not time_dir.is_file():
        print("\n################################################################")
        print("Running the " + time_dir.name + " case")
        print("################################################################\n")

        # Create the corresponding directories
        output_dir_final_path = manage_files.create_output_dir(
            input_dir_path,
            output_dir_path,
            time_dir,
            args.replay_dynawo,
            HADES_FOLDER,
            DYNAWO_FOLDER,
        )

        # Define if there will be the last "folder level" depending on whether the execution is reused
        # or if a new one has to be done.
        if args.calc_contingencies:
            time_dir_hades = time_dir / HADES_FOLDER
        else:
            if set([HADES_FOLDER, DYNAWO_FOLDER]).issubset(
                set([i.name for i in time_dir.iterdir()])
            ):
                time_dir_hades = time_dir / HADES_FOLDER
            else:
                time_dir_hades = time_dir

        # Run the contingencies with the specified hades launcher
        hades_input_file, hades_output_file, status = run_hades_contingencies_code(
            time_dir_hades,
            output_dir_final_path / HADES_FOLDER,
            hades_launcher_solved,
            args.tap_changers,
            args.multithreading,
            args.calc_contingencies,
        )

        # If the above function fails, exit the snapshot iteration without terminating execution.
        if status == 1:
            return

        # Rank all contingencies based of the hades simulation results
        sorted_loadflow_score_list, status = create_contingencies_ranking_code(
            hades_input_file,
            hades_output_file,
            output_dir_final_path,
            args.score_type,
            args.tap_changers,
        )

        # If the above function fails, exit the snapshot iteration without terminating execution.
        if status == 1:
            return

        # Show the ranking results
        display_results_table(output_dir_final_path, sorted_loadflow_score_list, args.tap_changers)

        # If selected, replay the worst contingencies with Dynawo systematic analysis
        if args.replay_dynawo:
            # Define if there will be the last "folder level" depending on whether the execution is
            # reused or if a new one has to be done.
            if args.calc_contingencies:
                dynawo_input_dir = time_dir / DYNAWO_FOLDER
            else:
                if set([HADES_FOLDER, DYNAWO_FOLDER]).issubset(
                    set([i.name for i in time_dir.iterdir()])
                ):
                    dynawo_input_dir = time_dir / DYNAWO_FOLDER
                else:
                    dynawo_input_dir = time_dir
            dynawo_output_dir = output_dir_final_path / DYNAWO_FOLDER

            # Create the path to the dynamic database if provided
            if args.dynamic_database is not None:
                dynamic_database = Path(args.dynamic_database).absolute()
            else:
                dynamic_database = None

            # Prepare the necessary files
            config_file, contng_file, matching_contng_dict, status = prepare_dynawo_SA(
                hades_input_file,
                sorted_loadflow_score_list,
                dynawo_input_dir,
                dynawo_output_dir,
                args.n_replay,
                dynamic_database,
                args.multithreading,
            )

            # If the above function fails, exit the snapshot iteration without terminating execution.
            if status == 1:
                return

            # Run the contingencies again
            status = run_dynawo_contingencies_SA_code(
                dynawo_input_dir,
                dynawo_output_dir,
                dynawo_launcher_solved,
                config_file,
                contng_file,
                args.calc_contingencies,
                matching_contng_dict,
            )

            # If the above function fails, exit the snapshot iteration without terminating execution.
            if status == 1:
                return

            # Clean Dynawo output results to save space, taking into account that mass executions will
            # be done and keeping all the information for a possible replay.
            if args.compress_results:
                manage_files.clean_data(
                    dynawo_output_dir,
                    sorted_loadflow_score_list,
                    args.n_replay,
                )

            # Extract dynawo results data
            dynawo_contingency_data = extract_dynawo_results(
                dynawo_output_dir, sorted_loadflow_score_list, args.n_replay
            )

            # Calc diffs between dynawo and hades
            df_diffs = calculate_case_differences(
                sorted_loadflow_score_list,
                dynawo_contingency_data,
                matching_contng_dict,
            )

            # Add new df_diffs columns to main contingencies DataFrame
            df_contg = pd.read_csv(
                output_dir_final_path / "contg_df.csv", sep=";", index_col="NUM"
            )
            df_contg = pd.merge(df_contg, df_diffs, how="left", on="NAME")

            # Sort by REAL_SCORE column and save to csv file
            df_contg = df_contg.sort_values("REAL_SCORE", ascending=False)

            if args.n_replay != -1:
                rmse = calc_case_diffs.calc_rmse(df_contg.head(args.n_replay))
                print()
                print(
                    "RMSE of the "
                    + str(args.n_replay)
                    + " most interesting contingencies (predicted vs real diff score without divergence cases):\n"
                    + str(rmse)
                )
            else:
                rmse = calc_case_diffs.calc_rmse(df_contg)
                print()
                print(
                    "RMSE of the all the contingencies (predicted vs real diff score without divergence cases):\n"
                    + str(rmse)
                )

            df_contg.to_csv(output_dir_final_path / "contg_df.csv", index=False, sep=";")

        # If selected, replay the worst contingencies with Hades one by one
        if args.replay_hades_obo:
            # Prepare the necessary files
            replay_hades_paths = prepare_hades_contingencies(
                sorted_loadflow_score_list,
                hades_input_file,
                hades_output_file.parent,
                args.n_replay,
            )

            # Run the contingencies again
            for replay_hades_path in replay_hades_paths:
                hades_input_file, hades_output_file, status = run_hades_contingencies_code(
                    replay_hades_path,
                    replay_hades_path,
                    hades_launcher_solved,
                    args.tap_changers,
                    args.multithreading,
                    False,
                )

        # If the option is selected and the execution has finished successfully, compress the results
        # to save space
        if args.compress_results:
            manage_files.compress_results(output_dir_final_path)


# FROM HERE:
# command line executables


def run_contingencies_screening():
    # Main execution pipeline
    args = argument_parser(
        [
            "input_dir",
            "output_dir",
            "hades_launcher",
            "dynawo_launcher",
            "tap_changers",
            "replay_hades_obo",
            "replay_dynawo",
            "n_replay",
            "score_type",
            "dynamic_database",
            "multithreading",
            "calc_contingencies",
            "compress_results",
        ]
    )
    input_dir_path = Path(args.input_dir).absolute()
    output_dir_path = Path(args.output_dir).absolute()

    # Check the existence of the input and output directories
    dir_exists(input_dir_path, output_dir_path)

    # Check if specified launchers are files in the system path or directories to files
    hades_launcher_solved = solve_launcher(Path(args.hades_launcher))
    dynawo_launcher_solved = solve_launcher(Path(args.dynawo_launcher))

    # Iterate through the different directories to execute all the cases provided, following
    # the structure of YEAR -> MONTH -> DAY -> HOUR
    for year_dir in input_dir_path.iterdir():
        if year_dir.is_file():
            continue
        for month_dir in year_dir.iterdir():
            if month_dir.is_file():
                continue
            for day_dir in month_dir.iterdir():
                if day_dir.is_file():
                    continue
                # Use or not multithreading depending on the selected option
                if args.multithreading:
                    arguments_list = []
                    for time_dir in day_dir.iterdir():
                        arguments_list.append(
                            (
                                args,
                                time_dir,
                                input_dir_path,
                                output_dir_path,
                                hades_launcher_solved,
                                dynawo_launcher_solved,
                            )
                        )

                    # Create a multiprocessing pool with the specified number of threads
                    pool = multiprocessing.Pool(processes=manage_files.N_THREADS_SNAPSHOT)

                    # Use starmap to call the function with different arguments in parallel
                    pool.starmap(run_contingencies_screening_thread_loop, arguments_list)

                    # Close the pool to prevent further tasks from being submitted
                    pool.close()

                    # Wait for all processes to finish
                    pool.join()

                else:
                    for time_dir in day_dir.iterdir():
                        run_contingencies_screening_thread_loop(
                            args,
                            time_dir,
                            input_dir_path,
                            output_dir_path,
                            hades_launcher_solved,
                            dynawo_launcher_solved,
                        )
