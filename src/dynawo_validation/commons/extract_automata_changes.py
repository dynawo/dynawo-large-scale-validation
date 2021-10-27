#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (c) Grupo AIA
#     marinjl@aia.es
#
#
# extract_automata_changes.py: Once a case has been run in Astre and Dynawo,
# this script extracts all relevant changes in control automata and writes them out
# to a couple of files, for later analysis. This output is standardized so that the
# event types and the devices they refer to use the same labels, so that a comparison
# can be made.
#
# On input, the script takes a directory containing both an Astre case and a Dynawo
# case, both of which have been simulated. For example, with the following structure
# (not strict, read below):
#
# RUN_CASE/
# ├── Astre
# │   └── donneesModelesEntree.xml
# ├── fic_JOB.xml
# ├── t0
# │   ├── fic_CRV.xml
# │   ├── fic_DYD.xml
# │   ├── fic_IIDM.xml
# │   └── fic_PAR.xml
# └── tFin
#    ├── fic_CRV.xml
#    ├── fic_DYD.xml
#    ├── fic_IIDM.xml
#    └── fic_PAR.xml
#
# Plus, of course, all the *output* files and directories generated by Astre and
# Dynawo. For Astre, the structure should be strictly as the above example.  However,
# for Dynawo we read the actual paths from the existing JOB file.
#
#
# On output, the script generates two new output files:
#
# RUN_CASE/
# ├── Astre
# │   └── Astre_aut_changes.csv
# └── Dynawo_aut_changes.csv
#
# These output files have the following columns:
#
#    DEVICE_TYPE; DEVICE; TIME; EVENT; EVENT_MESSAGE
#
# where the EVENT labels are standardized (i.e., translated) to those
# of Dynawo, while EVENT_MESSAGE keeps the original message, for
# reference.
#

import os
import sys
from collections import namedtuple
import pandas as pd
from dynawo_validation.dynawaltz.pipeline.dwo_jobinfo import (
    is_astdwo,
    is_dwodwo,
    is_dwohds,
    get_dwo_jobpaths,
    get_dwodwo_jobpaths,
)
from lxml import etree

ASTRE_EVENTS_IN = "/Astre/donneesModelesSortie.xml"
HADES_EVENTS_IN = "/Hades/out.xml"
ASTRE_EVENTS_OUT = "/Astre/Astre_automata_changes.csv"
HADES_EVENTS_OUT = "/Hades/Hades_automata_changes.csv"
DYNAWO_TIMELINE = "/timeLine/timeline.xml"  # to be prefixed with output path from JOB
DYNAWO_EVENTS_OUT = "/Dynawo_automata_changes.csv"
DYNAWO_A_EVENTS_OUT = "/DynawoA_automata_changes.csv"
DYNAWO_B_EVENTS_OUT = "/DynawoB_automata_changes.csv"

devtype_xfmer = "Transformer"
devtype_loadxfmer = "Load_Transformer"
devtype_shunt = "Shunt"
devtype_shuntctrl = "Shunt_Control"
devtype_klevel = "K_level"

verbose = True


def main():

    if len(sys.argv) != 3:
        print("\nUsage: %s run_case results_dir\n" % sys.argv[0])
        return 2
    run_case = sys.argv[1]
    results_dir = sys.argv[2]

    if verbose:
        print("Extracting automata changes for case: %s" % run_case)

    # Manage here whether it is an Astre-vs-Dynawo or a DynawoA-vs-DynawoB case
    if is_astdwo(run_case):
        launcherA, launcherB = find_launchers(results_dir)
        # construct Dynawo paths from the info in the JOB file
        dwo_paths = get_dwo_jobpaths(run_case)
        dwo_events_in = "/" + dwo_paths.outputs_directory + DYNAWO_TIMELINE
        dyd_file = "/" + dwo_paths.dydFile
        check_inputfiles(run_case, ASTRE_EVENTS_IN, dwo_events_in)
        # Extract the events from Astre results
        df_ast = extract_astre_events(run_case + ASTRE_EVENTS_IN)
        # Extract the events from Dynawo results
        df_dwo = extract_dynawo_events(run_case + dwo_events_in, run_case + dyd_file)
        # Sort and save
        if launcherA[:5] == "astre":
            save_extracted_events(
                df_ast,
                df_dwo,
                run_case + ASTRE_EVENTS_OUT,
                run_case + DYNAWO_EVENTS_OUT,
            )
        else:
            save_extracted_events(
                df_dwo,
                df_ast,
                run_case + DYNAWO_EVENTS_OUT,
                run_case + ASTRE_EVENTS_OUT,
            )
    elif is_dwohds(run_case):
        launcherA, launcherB = find_launchers(results_dir)
        # construct Dynawo paths from the info in the JOB file
        dwo_paths = get_dwo_jobpaths(run_case)
        dwo_events_in = "/" + dwo_paths.outputs_directory + DYNAWO_TIMELINE
        dyd_file = "/" + dwo_paths.dydFile
        check_inputfiles(run_case, HADES_EVENTS_IN, dwo_events_in)
        # Extract the events from Hades results
        df_hds = extract_astre_events(run_case + HADES_EVENTS_IN)
        # Extract the events from Dynawo results
        df_dwo = extract_dynawo_events(run_case + dwo_events_in, run_case + dyd_file)
        # Sort and save
        if launcherA[:5] == "hades":
            save_extracted_events(
                df_hds,
                df_dwo,
                run_case + HADES_EVENTS_OUT,
                run_case + DYNAWO_EVENTS_OUT,
            )
        else:
            save_extracted_events(
                df_dwo,
                df_hds,
                run_case + DYNAWO_EVENTS_OUT,
                run_case + HADES_EVENTS_OUT,
            )
                    
    elif is_dwodwo(run_case):
        # construct Dynawo paths from the info in the JOB_A and JOB_B files
        dwo_pathsA, dwo_pathsB = get_dwodwo_jobpaths(run_case)
        dwo_events_inA = "/" + dwo_pathsA.outputs_directory + DYNAWO_TIMELINE
        dwo_events_inB = "/" + dwo_pathsB.outputs_directory + DYNAWO_TIMELINE
        dyd_fileA = "/" + dwo_pathsA.dydFile
        dyd_fileB = "/" + dwo_pathsB.dydFile
        check_inputfiles(run_case, dwo_events_inA, dwo_events_inB)
        # Extract the events from Dynawo A & B results
        df_dwoA = extract_dynawo_events(run_case + dwo_events_inA, run_case + dyd_fileA)
        df_dwoB = extract_dynawo_events(run_case + dwo_events_inB, run_case + dyd_fileB)
        # Sort and save
        save_extracted_events(
            df_dwoA,
            df_dwoB,
            run_case + DYNAWO_A_EVENTS_OUT,
            run_case + DYNAWO_B_EVENTS_OUT,
        )
    else:
        raise ValueError("Case %s is neither an ast-dwo nor a dwo-dwo case" % run_case)

    return 0


def find_launchers(pathtofiles):
    launcherA = None
    launcherB = None
    for file in os.listdir(pathtofiles):
        basefile = os.path.basename(file)
        if ".LAUNCHER_A_WAS_" == basefile[:16] and launcherA == None:
            launcherA = basefile[16:]
        elif ".LAUNCHER_A_WAS_" == basefile[:16]:
            raise ValueError(f"Two or more .LAUNCHER_WAS_A in results dir")
        elif ".LAUNCHER_B_WAS_" == basefile[:16] and launcherB == None:
            launcherB = basefile[16:]
        elif ".LAUNCHER_B_WAS_" == basefile[:16]:
            raise ValueError(f"Two or more .LAUNCHER_WAS_A in results dir")
    return launcherA, launcherB


def check_inputfiles(run_case, events_in_1, events_in_2):
    if not os.path.isdir(run_case):
        raise ValueError("case directory %s not found" % run_case)
    # remove trailing slash
    if run_case[-1] == "/":
        run_case = run_case[:-1]
    if not (
        os.path.isfile(run_case + events_in_1)
        and os.path.isfile(run_case + events_in_2)
    ):
        raise ValueError("the expected output files are missing in %s\n" % run_case)


def extract_astre_events(astre_input):
    tree = etree.parse(astre_input)
    root = tree.getroot()
    ns = etree.QName(root).namespace

    # We'll be using a dataframe for sorting
    column_list = ["DEVICE_TYPE", "DEVICE", "TIME", "EVENT", "EVENT_MESSAGE"]
    data = []

    # We enumerate all events and extract the types we need
    for event in root.iter("{%s}evtchronologie" % ns):
        # Transformer taps
        if event.get("type") == "9" and event.get("evenement") == "1":  # PRISEPLUS1
            append_astre_data(data, event, devtype_xfmer, "TapUp")
        elif event.get("type") == "9" and event.get("evenement") == "2":  # PRISEMOINS1
            append_astre_data(data, event, devtype_xfmer, "TapDown")
        # Load-Transformer taps
        if event.get("type") == "7" and event.get("evenement") == "1":  # PRISEPLUS1
            append_astre_data(data, event, devtype_loadxfmer, "TapUp")
        elif event.get("type") == "7" and event.get("evenement") == "2":  # PRISEMOINS1
            append_astre_data(data, event, devtype_loadxfmer, "TapDown")
        # Shunts
        elif (
            event.get("type") == "4" and event.get("evenement") == "21"
        ):  # ACMC_ENCLENCHEMENT
            append_astre_data(data, event, devtype_shunt, "ShuntConnected")
        elif (
            event.get("type") == "4" and event.get("evenement") == "22"
        ):  # ACMC_DECLENCHEMENT
            append_astre_data(data, event, devtype_shunt, "ShuntDisconnected")
        elif (
            event.get("type") == "4" and event.get("evenement") == "33"
        ):  # SMACC_ENCLENCHEMENT
            append_astre_data(data, event, devtype_shunt, "ShuntConnected")
        elif (
            event.get("type") == "4" and event.get("evenement") == "34"
        ):  # SMACC_DECLENCHEMENT
            append_astre_data(data, event, devtype_shunt, "ShuntDisconnected")
        # K-levels
        elif (
            event.get("type") == "2" and event.get("evenement") == "18"
        ):  # RST_CONSIGNE
            append_astre_data(data, event, devtype_klevel, "NewRstLevel")

    # Translate the device IDs to their names
    astre_id2name(data, root)

    df = pd.DataFrame(data, columns=column_list)
    return df


def append_astre_data(data, event, device_type, event_name):
    # The order should match the column list in caller
    data.append(
        [
            device_type,
            event.get("ouvrage"),
            float(event.get("instant")),
            event_name,
            event.get("message"),
        ]
    )


def astre_id2name(data, tree_root):
    ns = etree.QName(tree_root).namespace

    # Build a dict: num ==> nom (we need one for each type of device)
    xfmer_names = dict()
    for xfmer in tree_root.iter("{%s}quadripole" % ns):
        xfmer_names[xfmer.get("num")] = xfmer.get("nom")

    loadxfmer_names = dict()
    for loadxfmer in tree_root.iter("{%s}conso" % ns):
        loadxfmer_names[loadxfmer.get("num")] = loadxfmer.get("nom")

    shunt_names = dict()
    for shunt in tree_root.iter("{%s}shunt" % ns):
        shunt_names[shunt.get("num")] = shunt.get("nom")

    klevel_names = dict()
    for klevel in tree_root.iter("{%s}groupe" % ns):
        klevel_names[klevel.get("num")] = klevel.get("nom")

    # Now depending on device type (row[0]), translate the ouvrage id
    # to its name (row[1])
    for row in data:
        if row[0] == devtype_xfmer:
            row[1] = xfmer_names.get(row[1], "**ERROR***")
        elif row[0] == devtype_loadxfmer:
            row[1] = loadxfmer_names.get(row[1], "**ERROR***")
        elif row[0] == devtype_shunt:
            row[1] = shunt_names.get(row[1], "**ERROR***")
        elif row[0] == devtype_klevel:
            row[1] = klevel_names.get(row[1], "**ERROR***")


def extract_dynawo_events(dynawo_input, dynawo_dyd):
    tree = etree.parse(dynawo_input)
    root = tree.getroot()
    ns = etree.QName(root).namespace

    # We'll be using a dataframe for sorting
    column_list = ["DEVICE_TYPE", "DEVICE", "TIME", "EVENT", "EVENT_MESSAGE"]
    data = []

    # We enumerate all events and extract the types we need
    for event in root.iter("{%s}event" % ns):
        # Transformer and Load-Transformer taps
        if event.get("message") == "Tap +1":
            append_dynawo_data(data, event, devtype_xfmer, "TapUp")
        elif event.get("message") == "Tap -1":
            append_dynawo_data(data, event, devtype_xfmer, "TapDown")
        # Shunts
        elif event.get("message") == "SHUNT : connecting":
            append_dynawo_data(data, event, devtype_shunt, "ShuntConnected")
        elif event.get("message") == "SHUNT : disconnecting":
            append_dynawo_data(data, event, devtype_shunt, "ShuntDisconnected")
        elif event.get("message")[:19] == "VCS : shunt number ":
            if event.get("message")[-8:] == " closing":
                append_dynawo_data(data, event, devtype_shuntctrl, "AcmcShuntClosing")
            elif event.get("message")[-8:] == " opening":
                append_dynawo_data(data, event, devtype_shuntctrl, "AcmcShuntOpening")
        elif event.get("message")[:28] == "MVCS : closing shunt number ":
            append_dynawo_data(data, event, devtype_shuntctrl, "SmaccClosingDelayPast")
        elif event.get("message")[:28] == "MVCS : opening shunt number ":
            append_dynawo_data(data, event, devtype_shuntctrl, "SmaccOpeningDelayPast")
        # K-levels
        elif event.get("message")[:21] == "SVC Area : new level ":
            append_dynawo_data(data, event, devtype_klevel, "NewRstLevel")

    # Translate the dynamic model labels to their static device counterparts
    dynawo_id2name(data, dynawo_dyd)

    df = pd.DataFrame(data, columns=column_list)
    return df


def append_dynawo_data(data, event, device_type, event_name):
    # The order should match the column list in caller
    data.append(
        [
            device_type,
            event.get("modelName"),
            float(event.get("time")),
            event_name,
            event.get("message"),
        ]
    )


def dynawo_id2name(data, dynawo_dyd):
    tree = etree.parse(dynawo_dyd)
    root = tree.getroot()
    ns = etree.QName(root).namespace

    # Build a dict: "Dynamic model name" ==> "Static name" (one for ALL types)
    dm_names = dict()
    Dev_info = namedtuple("Dev_info", ["lib_name", "static_id"])
    for dm in root.iter("{%s}blackBoxModel" % ns):
        static_id = dm.get("staticId")
        if static_id is not None:
            dm_names[dm.get("id")] = Dev_info(
                lib_name=dm.get("lib"), static_id=static_id
            )

    # Now, depending on the device type (row[0]), translate the
    # dynamic model id (row[1]) to its static name
    for row in data:
        # It seems that many (all?) TapUp/TapDown messages coming from
        # Dynamic Models are actually load-transformers, not
        # transmission transformers. So we'll also change the device
        # type to its ddb model library name, to tell them apart.
        if row[0] == devtype_xfmer and row[1][:3] == "DM_":
            dm_libname = dm_names.get(row[1], ["ERROR", "ERROR"]).lib_name
            row[1] = dm_names.get(row[1], ["ERROR", "ERROR"]).static_id
            if dm_libname[:4] == "Load":
                row[0] = devtype_loadxfmer
            elif dm_libname[:11] != "Transformer":
                row[0] = dm_libname


def save_extracted_events(df_1, df_2, output_1, output_2):
    # Filter events. Use Panda's query() syntax (use None for no filter).
    # evt_filter = "DEVICE_TYPE in ['%s', '%s', '%s']" % (devtype_xfmer,
    # devtype_loadxfmer, devtype_shunt)
    evt_filter = "DEVICE_TYPE in ['%s', '%s', '%s']" % (
        devtype_xfmer,
        devtype_loadxfmer,
        devtype_shunt,
    )
    if evt_filter is not None:
        df_1 = df_1.query(evt_filter)
        df_2 = df_2.query(evt_filter)

    # Sort dataframe
    sort_fields = ["DEVICE_TYPE", "DEVICE", "TIME"]
    sort_order = [True, True, True]
    df_1 = df_1.sort_values(
        by=sort_fields, ascending=sort_order, inplace=False, na_position="first"
    )
    df_2 = df_2.sort_values(
        by=sort_fields, ascending=sort_order, inplace=False, na_position="first"
    )

    # Save to file
    df_1.to_csv(output_1, index=False, sep=";", encoding="utf-8")
    df_2.to_csv(output_2, index=False, sep=";", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
