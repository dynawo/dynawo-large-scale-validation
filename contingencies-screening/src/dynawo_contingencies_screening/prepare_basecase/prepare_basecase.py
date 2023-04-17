import os
import argparse
from pathlib import Path
import pandas as pd


def parser(args_type):
    p = argparse.ArgumentParser()
    if args_type == 1:
        p.add_argument(
            "case_dir",
            help="enter the path to the folder containing the case files",
        )
    if args_type == 2:
        p.add_argument(
            "job_file",
            help="TODO: explain",
        )
        p.add_argument(
            "pepito",
            help="TODO: explain",
        )

    args = p.parse_args()
    return args


def xml_format_dir():
    args = parser(1)

    os.system(
        str(Path(os.path.dirname(os.path.abspath(__file__))))
        + "/xml_format_dir.sh "
        + str(Path(args.case_dir))
    )


def format_job_file():
    args = parser(2)

    os.system(
        str(Path(os.path.dirname(os.path.abspath(__file__))))
        + "/xml_format_dir.sh "
        + str(Path(args.case_dir))
    )


if __name__ == "__main__":
    format_job_file()
