import os
from pathlib import Path
import shutil


def run_hades_basecase(hades_input_file, hades_output_file, hades_launcher):
    # Get the output folder (using hades_output_file parent folder) to be able to copy the input file
    # into the ouputs folder, and with this last file (copy of the input located in the output folder),
    # run hades through Python with the launcher provided in the arguments, leaving the result in the
    # hades_output_file

    # We obtain the output folder path
    # and copy the input file there
    output_folder = Path(hades_output_file).parent.absolute()
    shutil.copy(hades_input_file, output_folder)

    # Run the simulation on the specified hades launcher
    os.system(
        hades_launcher + " "
        + output_folder + hades_input_file
        + " " + hades_output_file
    )
