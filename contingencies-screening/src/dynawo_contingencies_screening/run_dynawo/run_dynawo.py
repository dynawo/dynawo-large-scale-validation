import os
import shutil
import subprocess


def run_dynaflow(input_dir, output_dir, dynawo_launcher):
    # From the data specified in the input directory,
    # run the simulation in the desired Dynawo launcher

    # We obtain the output folder path
    # and copy the input file there
    files = os.listdir(input_dir)

    for fname in files:
        shutil.copy2(input_dir / fname, output_dir)

    # Run the simulation on the specified dynawo launcher
    subprocess.run(
        str(dynawo_launcher) + " jobs " + str(output_dir) + "/JOB.xml ",
        shell=True,
        check=True,
    )
