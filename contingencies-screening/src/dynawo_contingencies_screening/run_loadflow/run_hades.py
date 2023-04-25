import shutil
import subprocess


def run_hades(hades_input_file, hades_output_file, hades_launcher):
    # Get the output folder (using hades_output_file parent folder) to be able to copy the input file
    # into the ouputs folder, and with this last file (copy of the input located in the output folder),
    # run hades through Python with the launcher provided in the arguments, leaving the result in the
    # hades_output_file

    # We obtain the output folder path
    # and copy the input file there
    output_folder = hades_output_file.parent
    shutil.copy(hades_input_file, output_folder)

    # Run the simulation on the specified hades launcher
    subprocess.run(
        str(hades_launcher)
        + " "
        + str(output_folder / (hades_input_file.name))
        + " "
        + str(hades_output_file),
        shell=True,
        check=True,
    )
