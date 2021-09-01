#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (c) Grupo AIA
#     gaitanv@aia.es
#     marinjl@aia.es
#
#
# generate_notebooks.py: a simple script to generate a Notebook per CASE. You only
# need to provide the base directory that contains the cases that have been run.
#

import sys
import argparse
import os
from pathlib import Path
import re

sys.path.insert(
    1, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

parser = argparse.ArgumentParser()

parser.add_argument("case_dir", help="enter case directory")
parser.add_argument("base_case", help="enter base case directory")
parser.add_argument("contg_type", help="enter contingency type")

args = parser.parse_args()


def is_dwohds(case):
    """Return true if an Hades subdirectory exists (Dynawo-vs-Hades case)"""
    casedir = Path(case)
    if not os.path.isdir(casedir):
        raise ValueError("Case directory %s not found" % casedir)
    return os.path.isdir(casedir / "Hades")


def is_dwodwo(case):
    """Return true if one JOB_A and one JOB_B files exist (Dynawo-vs-Dynawo case)"""
    casedir = Path(case)
    if not os.path.isdir(casedir):
        raise ValueError("Case directory %s not found" % casedir)
    jobfile_patternA = re.compile(r"JOB_A.*?\.xml$", re.IGNORECASE)
    match_A = [n for n in os.listdir(casedir) if jobfile_patternA.search(n)]
    jobfile_patternB = re.compile(r"JOB_B.*?\.xml$", re.IGNORECASE)
    match_B = [n for n in os.listdir(casedir) if jobfile_patternB.search(n)]
    return len(match_A) == 1 and len(match_B) == 1


def main():
    case_dir = args.case_dir
    base_case = args.base_case
    contg_type = args.contg_type

    if is_dwohds(base_case):
        dwo_dwo = "0"
    elif is_dwodwo(base_case):
        dwo_dwo = "1"
    else:
        raise ValueError(f"Case {base_case} is neither an dwo-hds nor a dwo-dwo case")

    if contg_type[-1] == "_":
        contg_type = contg_type[:-1]
    if base_case[-1] == "/":
        base_case = base_case[:-1]
    if case_dir[-1] != "/":
        case_dir = case_dir + "/"

    fin = open(sys.path[0] + "/simulator_A_vs_simulator_B.ipynb", "rt")
    # output file to write the result to
    fout = open(sys.path[0] + "/simulator_A_vs_simulator_B_final.ipynb", "wt")
    # for each line in the input file
    for line in fin:
        # read replace the string and write to output file
        if "PLACEHOLDER_RESULTS_DIR" in line:
            fout.write(line.replace("PLACEHOLDER_RESULTS_DIR", case_dir))
        elif "PLACEHOLDER_BASECASE" in line:
            fout.write(line.replace("PLACEHOLDER_BASECASE", base_case))
        elif "PLACEHOLDER_PREFIX" in line:
            fout.write(line.replace("PLACEHOLDER_PREFIX", contg_type))
        elif "PLACEHOLDER_DWO_DWO" in line:
            fout.write(line.replace("PLACEHOLDER_DWO_DWO", dwo_dwo))
        else:
            fout.write(line)
    # close input and output files
    fin.close()
    fout.close()


if __name__ == "__main__":
    sys.exit(main())
