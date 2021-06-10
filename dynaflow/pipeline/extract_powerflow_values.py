#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (c) Grupo AIA
#     marinjl@aia.es
#
#
# extract_powerflow_values.py: Once a case has been run in Hades and DynaFlow,
# this script extracts all relevant values of the resulting steady state, for the
# purpose of comparing both solutions in later analysis. In the output, the device
# types, IDs, and variable names all use their Dynawo version.
#
# On input, the script takes a directory containing both an Hades and a DynaFlow
# power-flow case, both of which have already been run. For now, the following dir
# structure is assumed:
#
#   CASE_DIR/
#   ├── Hades
#   │   └── *.xml
#   ├── <dynaflow_case>.jobs
#   ├── <dynaflow_case>.xiidm
#   ├── <dynaflow_case>.dyd
#   ├── <dynaflow_case>.par
#   ├── Network.par
#   └── solver.par
# (Plus, of course, all the *output* files and dirs generated by Hades and Dynawo)
#
#
# On output, the script generates one main output file and (possibly) two error files:
#
#   CASE_DIR/
#   ├── pfsolution_AB.csv.xz
#   ├── ERRORS-elements_not_in_caseA.csv.xz
#   └── ERRORS-elements_not_in_caseB.csv.xz
#
# The output file has the following columns:
#
#    ["ID", "ELEMENT_TYPE", "VAR", "VOLT_LEVEL", "VALUE_A", "VALUE_B"]
#
# where we use the VAR names used in Dynawo.
#

import os
import math
import sys
import pandas as pd
from lxml import etree
from collections import namedtuple

# import itertools

HDS_INPUT = "/Hades/donneesEntreeHADES2.xml"
HDS_SOLUTION = "/Hades/out.xml"
DYNAWO_SOLUTION = "/finalState/outputIIDM.xml"
DYNAWO_OUTPUTS_DIR = "/outputs"  # TODO: extract from JOB file instead
OUTPUT_FILE = "/pfsolution_AB.csv.xz"
ERRORS_A_FILE = "/FILTERED-elements_not_in_caseA.csv.xz"
ERRORS_B_FILE = "/FILTERED-elements_not_in_caseB.csv.xz"
ZEROPQ_TOL = 1.0e-5  # inactivity detection: flows below this (in MW) considered zero

# named tuples
Branch_info = namedtuple("Branch_info", ["type", "bus1", "bus2"])
Branch_side = namedtuple("Branch_side", ["bus1", "bus2"])
verbose = True


def main():

    if len(sys.argv) != 2:
        print(f"\nUsage: {sys.argv[0]} case_dir\n")
        return 2
    case_dir = sys.argv[1]

    if verbose:
        print(f"Extracting solution values for case: {case_dir}")

    # TODO: Manage here whether it is a Hades-vs-Dynawo or a DynawoA-vs-DynawoB case
    # if is_astdwo(case_dir):
    # elif is_dwodwo(case_dir):
    # else: raise ValueError(f"Case {case_dir} is neither a hds-dwo nor a dwo-dwo case")

    # TODO: construct Dynawo paths from the info in the JOB file
    # dwo_paths = get_dwo_jobpaths(case_dir)
    # dwo_soln = "/" + dwo_paths.outputs_directory + DYNAWO_OUTPUT_FILE
    dwo_solution = DYNAWO_OUTPUTS_DIR + DYNAWO_SOLUTION
    check_inputfiles(case_dir, HDS_SOLUTION, dwo_solution)

    # Extract the solution values from Dynawo results
    df_dwo, vl_nomV, branch_info = extract_dynawo_output(case_dir + dwo_solution)

    # Extract the solution values from Hades results
    df_hds = extract_hades_output(
        case_dir + HDS_SOLUTION, case_dir + HDS_INPUT, vl_nomV, branch_info
    )

    # Merge, sort, and save
    save_extracted_values(df_dwo, df_hds, case_dir + OUTPUT_FILE)
    save_nonmatching_elements(
        df_dwo, df_hds, case_dir + ERRORS_A_FILE, case_dir + ERRORS_B_FILE
    )

    return 0


def check_inputfiles(case_dir, solution_1, solution_2):
    if not os.path.isdir(case_dir):
        raise ValueError(f"case directory {case_dir} not found")
    if not (
        os.path.isfile(case_dir + solution_1) and os.path.isfile(case_dir + solution_2)
    ):
        raise ValueError(f"the expected PF solution files are missing in {case_dir}\n")


def extract_dynawo_output(dynawo_output, vl_nomv=None, branches=None):
    """Read all output and return a dataframe. If case_A, create vl_nomv & branches"""
    tree = etree.parse(dynawo_output)
    root = tree.getroot()
    # Manage whether we're case A or B, when used for Dynawo-vs-Dynawo
    if vl_nomv is None:
        is_case_A = True
        value_col = "VALUE_A"
        # we will build an aux dict (bus --> volt level) as we traverse buses below
        vl_nomv = dict()
        # and another aux dict for the branches, containing this Branch_info:
        #    * type, for disambiguating HADES quadripoles later on
        #    * buses on each side, to avoid inconsistencies in side-labeling convention
        branches = dict()
    else:
        is_case_A = False
        value_col = "VALUE_B"
    # We'll be using a dataframe, for sorting
    column_list = ["ID", "ELEMENT_TYPE", "VOLT_LEVEL", "VAR", value_col]
    data = []
    print("   found in Dynawo file:", end="")
    # Buses: get V & angle
    extract_dwo_buses(root, is_case_A, data, vl_nomv)
    # Lines: p & q flows
    extract_dwo_lines(root, is_case_A, data, vl_nomv, branches)
    # Transformers and phase shifters: p & q flows
    extract_dwo_xfmrs(root, is_case_A, data, vl_nomv, branches)
    # Aggregate bus injections (loads, generators, shunts, VSCs)
    extract_dwo_bus_inj(root, data, vl_nomv)
    return pd.DataFrame(data, columns=column_list), vl_nomv, branches


def extract_dwo_buses(root, is_case_a, data, vl_nomv):
    """Read V & angles, and update data. Also update the vl_nomv dict if it's case_A"""
    ctr = 0
    for bus in root.iterfind(".//bus", root.nsmap):
        bus_name = bus.get("id")
        v = bus.get("v")
        angle = bus.get("angle")
        # build the voltlevel dict *before* skipping inactive buses
        if is_case_a:
            vl_nomv[bus_name] = int(bus.getparent().getparent().get("nominalV"))
        # skip inactive buses
        if v == "0" and angle == "0":
            continue
        volt_level = vl_nomv[bus_name]
        data.append([bus_name, "bus", volt_level, "v", float(v)])
        data.append([bus_name, "bus", volt_level, "angle", float(angle)])
        ctr += 1
    print(f" {ctr:5d} buses", end="")


def extract_dwo_lines(root, is_case_a, data, vl_nomv, branches):
    """Read line flows, and update data. Also update branches dict if it's case_A"""
    ctr = 0
    for line in root.iterfind("./line", root.nsmap):
        line_name = line.get("id")
        p1 = float(line.get("p1"))
        q1 = float(line.get("q1"))
        p2 = float(line.get("p2"))
        q2 = float(line.get("q2"))
        # build the branches dict *before* skipping inactive lines
        if is_case_a:
            branches[line_name] = Branch_info(
                type="line",
                bus1=line.get("connectableBus1"),
                bus2=line.get("connectableBus2"),
            )
        # skip inactive lines (beware threshold effect when comparing to the other case)
        if (
            abs(p1) < ZEROPQ_TOL
            and abs(q1) < ZEROPQ_TOL
            and abs(p2) < ZEROPQ_TOL
            and abs(q2) < ZEROPQ_TOL
        ):
            continue
        volt_level = vl_nomv[line.get("connectableBus1")]
        element_type = branches[line_name].type
        data.append([line_name, element_type, volt_level, "p1", p1])
        data.append([line_name, element_type, volt_level, "q1", q1])
        data.append([line_name, element_type, volt_level, "p2", p2])
        data.append([line_name, element_type, volt_level, "q2", q2])
        ctr += 1
    print(f" {ctr:5d} lines", end="")


def extract_dwo_xfmrs(root, is_case_a, data, vl_nomv, branches):
    """Read xfmr flows & taps, and update data. Also update branches dict, if case_A"""
    ctr, psctr = [0, 0]
    for xfmr in root.iterfind(".//twoWindingsTransformer", root.nsmap):
        xfmr_name = xfmr.get("id")
        p1 = float(xfmr.get("p1"))
        q1 = float(xfmr.get("q1"))
        p2 = float(xfmr.get("p2"))
        q2 = float(xfmr.get("q2"))
        tap = xfmr.find("./ratioTapChanger", root.nsmap)
        ps_tap = xfmr.find("./phaseTapChanger", root.nsmap)
        # build branches dict *before* skipping inactive transformers
        if is_case_a:
            if ps_tap is not None:
                branches[xfmr_name] = Branch_info(
                    type="psxfmr",
                    bus1=xfmr.get("connectableBus1"),
                    bus2=xfmr.get("connectableBus2"),
                )
            else:
                branches[xfmr_name] = Branch_info(
                    type="xfmr",
                    bus1=xfmr.get("connectableBus1"),
                    bus2=xfmr.get("connectableBus2"),
                )
        # skip inactive xfmrs (beware threshold effect when comparing to the other case)
        if (
            abs(p1) < ZEROPQ_TOL
            and abs(q1) < ZEROPQ_TOL
            and abs(p2) < ZEROPQ_TOL
            and abs(q2) < ZEROPQ_TOL
        ):
            continue
        volt_level = vl_nomv[xfmr.get("connectableBus2")]  # side 2 assumed always HV
        data.append([xfmr_name, branches[xfmr_name].type, volt_level, "p1", p1])
        data.append([xfmr_name, branches[xfmr_name].type, volt_level, "q1", q1])
        data.append([xfmr_name, branches[xfmr_name].type, volt_level, "p2", p2])
        data.append([xfmr_name, branches[xfmr_name].type, volt_level, "q2", q2])
        # transformer taps
        if tap is not None:
            data.append(
                [
                    xfmr_name,
                    branches[xfmr_name].type,
                    volt_level,
                    "tap",
                    int(tap.get("tapPosition")),
                ]
            )
        # phase-shifter taps
        if ps_tap is not None:
            data.append(
                [
                    xfmr_name,
                    branches[xfmr_name].type,
                    volt_level,
                    "pstap",
                    int(ps_tap.get("tapPosition")),
                ]
            )
        # counters
        if branches[xfmr_name].type == "psxfmr":
            psctr += 1
        else:
            ctr += 1
    print(f" {ctr:5d} xfmrs", end="")
    print(f" {psctr:3d} psxfmrs", end="")


def extract_dwo_bus_inj(root, data, vl_nomv):
    """Aggregate injections (loads, gens, shunts, VSCs) by bus, and update data."""
    # Since a voltage level may contain more than one bus, it is easier to keep the
    # aggregate injections in dicts indexed by bus, and then output at the end.
    p_inj = dict()
    q_inj = dict()
    for vl in root.iterfind(".//voltageLevel", root.nsmap):
        # loads
        for load in vl.iterfind("./load", root.nsmap):
            bus_name = load.get("bus")
            if bus_name is not None:
                p_inj[bus_name] = p_inj.get(bus_name, 0.0) + float(load.get("p"))
                q_inj[bus_name] = q_inj.get(bus_name, 0.0) + float(load.get("q"))
        # generators
        for gen in vl.iterfind("./generator", root.nsmap):
            bus_name = gen.get("bus")
            if bus_name is not None:
                p_inj[bus_name] = p_inj.get(bus_name, 0.0) + float(gen.get("p"))
                q_inj[bus_name] = q_inj.get(bus_name, 0.0) + float(gen.get("q"))
        # shunts
        for shunt in vl.iterfind("./shunt", root.nsmap):
            bus_name = shunt.get("bus")
            if bus_name is not None:
                q_inj[bus_name] = q_inj.get(bus_name, 0.0) + float(shunt.get("q"))
        # VSCs
        for vsc in vl.iterfind("./vscConverterStation", root.nsmap):
            bus_name = vsc.get("bus")
            if bus_name is not None:
                p_inj[bus_name] = p_inj.get(bus_name, 0.0) + float(vsc.get("p"))
                q_inj[bus_name] = q_inj.get(bus_name, 0.0) + float(vsc.get("q"))
        # SVCs
        for vsc in vl.iterfind("./staticVarCompensator", root.nsmap):
            bus_name = vsc.get("bus")
            if bus_name is not None:
                p_inj[bus_name] = p_inj.get(bus_name, 0.0) + float(vsc.get("p"))
                q_inj[bus_name] = q_inj.get(bus_name, 0.0) + float(vsc.get("q"))

    # update data
    for bus_name in p_inj:
        p = p_inj[bus_name]
        if abs(p) > ZEROPQ_TOL:
            data.append([bus_name, "bus", vl_nomv[bus_name], "p", p])
    for bus_name in q_inj:
        q = q_inj[bus_name]
        if abs(q) > ZEROPQ_TOL:
            data.append([bus_name, "bus", vl_nomv[bus_name], "q", q])
    print("                         ", end="")  # Hades has extra output here
    print(f" {len(p_inj):5d} P-injections", end="")
    print(f" {len(q_inj):5d} Q-injections")


def extract_hades_output(hades_output, hades_input, vl_nomv, dwo_branches):
    """Read all output and return a dataframe."""
    tree = etree.parse(hades_output)
    root = tree.getroot()
    # We'll be using a dataframe, for sorting
    column_list = ["ID", "ELEMENT_TYPE", "VAR", "VALUE_B"]
    data = []
    print("   found in Hades file:", end="")
    # Buses: get V & angle
    extract_hds_buses(root, vl_nomv, data)
    # Branches (line/xfmr/psxfmr): p & q flows and xfmr taps
    extract_hds_branches(hades_input, root, dwo_branches, data)
    # Aggregate bus injections (loads, generators, shunts, VSCs)
    extract_hds_bus_inj(root, data)
    return pd.DataFrame(data, columns=column_list)


def extract_hds_buses(root, vl_nomv, data):
    """Read V & angles, and update data."""
    reseau = root.find("./reseau", root.nsmap)
    donneesNoeuds = reseau.find("./donneesNoeuds", root.nsmap)
    ctr = 0
    for bus in donneesNoeuds.iterfind("./noeud", root.nsmap):
        bus_name = bus.get("nom")
        v = bus[0].get("v")
        angle = bus[0].get("ph")
        if v == "999999.000000000000000" and angle == "999999.000000000000000":
            continue  # skip inactive buses
        data.append([bus_name, "bus", "v", float(v) * vl_nomv[bus_name] / 100])
        data.append([bus_name, "bus", "angle", float(angle) * 180 / math.pi])
        ctr += 1
    print(f"  {ctr:5d} buses", end="")


def extract_hds_branches(hades_input, root, dwo_branches, data):
    """Read branch flows (incl. xfmr taps), and update data."""
    # These aux dicts need to be read from the *input* case (it's not in the output)
    hds_branch_sides, tap2xfmr, pstap2xfmr = extract_hds_gridinfo(hades_input)
    # now we can read everything else from the output file
    # first we extract tap and phase-shifter tap values (used below)
    taps, pstaps = extract_hds_taps(root, tap2xfmr, pstap2xfmr)
    # and now we extract the branch (quadripole) data
    lctr, xctr, psctr, bad_ctr = [0, 0, 0, 0]
    reseau = root.find("./reseau", root.nsmap)
    donneesQuadripoles = reseau.find("./donneesQuadripoles", root.nsmap)
    for quadrip in donneesQuadripoles.iterfind("./quadripole", root.nsmap):
        quadrip_name = quadrip.get("nom")
        p1 = float(quadrip[0].get("por"))
        q1 = float(quadrip[0].get("qor"))
        p2 = float(quadrip[0].get("pex"))
        q2 = float(quadrip[0].get("qex"))
        # magic number 999999 is used for disconnected branches
        if p1 > 999_990:
            p1 = 0.0
        if q1 > 999_990:
            q1 = 0.0
        if p2 > 999_990:
            p2 = 0.0
        if q2 > 999_990:
            q2 = 0.0
        # skip inactive lines
        if (
            abs(p1) < ZEROPQ_TOL
            and abs(q1) < ZEROPQ_TOL
            and abs(p2) < ZEROPQ_TOL
            and abs(q2) < ZEROPQ_TOL
        ):
            continue
        # find out whether it is a line/xfmr/psxfmr by looking it up in Dynawo case
        dwo_branch_info = dwo_branches.get(quadrip_name)
        if dwo_branch_info is not None:
            element_type = dwo_branch_info.type
            # and if side-labeling convention is reversed, fix it
            if hds_branch_sides[quadrip_name].bus1 == dwo_branch_info.bus2:
                p1, p2 = (p2, p1)
                q1, q2 = (q2, q1)
        else:
            element_type = "QUADRIPOLE_NOT_IN_DWO"
        # collect the data
        data.append([quadrip_name, element_type, "p1", p1])
        data.append([quadrip_name, element_type, "q1", q1])
        data.append([quadrip_name, element_type, "p2", p2])
        data.append([quadrip_name, element_type, "q2", q2])
        tap_value = taps.get(quadrip_name)
        if tap_value is not None:
            data.append([quadrip_name, element_type, "tap", tap_value])
        pstap_value = pstaps.get(quadrip_name)
        if pstap_value is not None:
            data.append([quadrip_name, element_type, "pstap", pstap_value])
        # counters
        if element_type == "line":
            lctr += 1
        elif element_type == "xfmr":
            xctr += 1
        elif element_type == "psxfmr":
            psctr += 1
        else:
            bad_ctr += 1
    print(
        f" {lctr:5d} lines {xctr:5d} xfmrs {psctr:3d} psxfmrs"
        f" ({bad_ctr} quadrip. not in Dwo)", end=""
    )


def extract_hds_gridinfo(hades_input):
    """Read info that's only available in the input file (branch buses; xfmr taps)."""
    tree = etree.parse(hades_input)
    root = tree.getroot()
    reseau = root.find("./reseau", root.nsmap)
    # auxiliary dict that maps "num" to "nom"
    buses = dict()
    donneesNoeuds = reseau.find("./donneesNoeuds", root.nsmap)
    for bus in donneesNoeuds.iterfind("./noeud", root.nsmap):
        buses[bus.get("num")] = bus.get("nom")
    buses["-1"] = "DISCONNECTED"
    # now build a dict that maps branch names to their bus1 and bus2 names
    branch_sides = dict()
    donneesQuadripoles = reseau.find("./donneesQuadripoles", root.nsmap)
    for branch in donneesQuadripoles.iterfind("./quadripole", root.nsmap):
        branch_sides[branch.get("nom")] = Branch_side(
            bus1=buses[branch.get("nor")], bus2=buses[branch.get("nex")]
        )
    # now build a dict that maps "regleur" IDs to their transformer's name
    # AND a dict that maps "dephaseur" IDs to their transformer's name
    tap2xfmr = dict()
    pstap2xfmr = dict()
    for branch in donneesQuadripoles.iterfind("./quadripole", root.nsmap):
        tap_ID = branch.get("ptrregleur")
        if tap_ID != "0" and tap_ID is not None:
            tap2xfmr[tap_ID] = branch.get("nom")
        pstap_ID = branch.get("ptrdepha")
        if pstap_ID != "0" and pstap_ID is not None:
            pstap2xfmr[pstap_ID] = branch.get("nom")
    return branch_sides, tap2xfmr, pstap2xfmr


def extract_hds_taps(root, tap2xfmr, pstap2xfmr):
    """Read tap values and return them in two dicts indexed by name (taps, pstaps)."""
    taps = dict()
    reseau = root.find("./reseau", root.nsmap)
    donneesRegleurs = reseau.find("./donneesRegleurs", root.nsmap)
    for regleur in donneesRegleurs.iterfind("./regleur", root.nsmap):
        quadrip_name = tap2xfmr.get(regleur.get("num"))
        if quadrip_name is None:
            raise ValueError(
                f"in Hades output file: regleur {regleur.get('num')}"
                "  has no associated transformer!"
            )
        taps[quadrip_name] = int(regleur.find("./variables", root.nsmap).get("plot"))
    # now phase-shifter taps
    pstaps = dict()
    donneesDephaseurs = reseau.find("./donneesDephaseurs", root.nsmap)
    for dephaseur in donneesDephaseurs.iterfind("./dephaseur", root.nsmap):
        quadrip_name = pstap2xfmr.get(dephaseur.get("num"))
        if quadrip_name is None:
            raise ValueError(
                f"in Hades output file: dephaseur {dephaseur.get('num')}"
                "  has no associated transformer!"
            )
        pstaps[quadrip_name] = int(
            dephaseur.find("./variables", root.nsmap).get("plot")
        )
    return taps, pstaps


def extract_hds_bus_inj(root, data):
    """Aggregate injections (loads, gens, shunts, VSCs) by bus, and update data."""
    # Conveniently, Hades provides the bus injections in the bus output
    reseau = root.find("./reseau", root.nsmap)
    donneesNoeuds = reseau.find("./donneesNoeuds", root.nsmap)
    pctr, qctr = [0, 0]
    for bus in donneesNoeuds.iterfind("./noeud", root.nsmap):
        bus_name = bus.get("nom")
        bus_vars = bus.find("./variables", root.nsmap)
        if (
            bus_vars.get("v") == "999999.000000000000000"
            and bus_vars.get("ph") == "999999.000000000000000"
        ):
            continue  # skip inactive buses
        # update data (note the opposite sign convention w.r.t. Dynawo)
        p = - float(bus_vars.get("injact"))
        if abs(p) > ZEROPQ_TOL:
            data.append([bus_name, "bus", "p", p])
            pctr += 1
        q = - float(bus_vars.get("injrea"))
        if abs(q) > ZEROPQ_TOL:
            data.append([bus_name, "bus", "q", q])
            qctr += 1
    print(f" {pctr:5d} P-injections", end="")
    print(f" {qctr:5d} Q-injections")


def save_extracted_values(df_a, df_b, output_file):
    """Save the values for all elements that are matched in both outputs."""
    # Merge (inner join) the two dataframes, checking for duplicates (just in case)
    key_fields = ["ELEMENT_TYPE", "ID", "VAR"]
    df = pd.merge(df_a, df_b, how="inner", on=key_fields, validate="one_to_one")
    # Print some summaries
    print("   common to both files:", end="")
    bus_angles = (df["ELEMENT_TYPE"] == "bus") & (df["VAR"] == "angle")
    print(f" {len(df.loc[bus_angles]):5d} buses", end="")
    lines_p1 = (df["ELEMENT_TYPE"] == "line") & (df["VAR"] == "p1")
    print(f" {len(df.loc[lines_p1]):5d} lines", end="")
    xfmr_p1 = (df["ELEMENT_TYPE"] == "xfmr") & (df["VAR"] == "p1")
    print(f" {len(df.loc[xfmr_p1]):5d} xfmrs", end="")
    psxfmr_p1 = (df["ELEMENT_TYPE"] == "psxfmr") & (df["VAR"] == "p1")
    print(f" {len(df.loc[psxfmr_p1]):3d} psxfmrs")
    # Adjust the bus angles to those of solution A
    swing_idx = df.loc[bus_angles, "VALUE_A"].abs().idxmin()
    angle_offset = df.at[swing_idx, "VALUE_B"] - df.at[swing_idx, "VALUE_A"]
    df.loc[bus_angles, "VALUE_B"] -= angle_offset
    print(f'   (angle offset adjusted; zero angle at bus: {df.at[swing_idx, "ID"]})')
    # Sort and save to file
    sort_order = [True, True, True]
    df.sort_values(
        by=key_fields, ascending=sort_order, inplace=True, na_position="first"
    )
    df.to_csv(output_file, index=False, sep=";", encoding="utf-8", compression="xz")
    print(f"Saved output to file: {output_file}... ")


def save_nonmatching_elements(df_a, df_b, errors_a_file, errors_b_file):
    """Save the elements that did not match. Some may be due to threshold flows."""
    key_fields = ["ELEMENT_TYPE", "ID", "VAR"]
    # Output the diffs. Newer versions of Pandas support df.compare(), but here we do
    # it in a more backwards-compatible way.
    set_A = frozenset(df_a["ID"].add(df_a["ELEMENT_TYPE"]))
    set_B = frozenset(df_b["ID"].add(df_b["ELEMENT_TYPE"]))
    elements_not_in_A = list(set_B - set_A)
    elements_not_in_B = list(set_A - set_B)
    if len(elements_not_in_A) != 0:
        df_not_in_A = df_b.loc[
            (df_b["ID"] + df_b["ELEMENT_TYPE"]).isin(elements_not_in_A)
        ]
        df_not_in_A.sort_values(by=key_fields, ascending=[True, True, True]).to_csv(
            errors_a_file, index=False, sep=";", encoding="utf-8", compression="xz"
        )
        print(
            f"{len(elements_not_in_A)} elements from case B not in case A "
            f"saved in file: {errors_a_file}"
        )
    if len(elements_not_in_B) != 0:
        df_not_in_B = df_a.loc[
            (df_a["ID"] + df_a["ELEMENT_TYPE"]).isin(elements_not_in_B)
        ]
        df_not_in_B.sort_values(by=key_fields, ascending=[True, True, True]).to_csv(
            errors_b_file, index=False, sep=";", encoding="utf-8", compression="xz"
        )
        print(
            f"{len(elements_not_in_B)} elements from case A not in case B "
            f"saved in file: {errors_b_file}"
        )


if __name__ == "__main__":
    sys.exit(main())
