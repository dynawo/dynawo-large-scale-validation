import shutil
import subprocess


def run_dynaflow(input_dir, output_dir, dynawo_launcher):
    # From the data specified in the input directory,
    # run the simulation in the desired Dynawo launcher

    # We obtain the output folder path
    # and copy the input file there
    for fname in input_dir.glob("**/*"):
        shutil.copy2(input_dir / fname, output_dir)

    # Run the simulation on the specified dynawo launcher
    subprocess.run(
        str(dynawo_launcher) + " jobs " + str(output_dir) + "/JOB.xml ",
        shell=True,
        check=True,
    )


def run_dynaflow_SA(input_dir, output_dir, dynawo_launcher, config_file, contng_file):
    # From the data specified in the input directory,
    # run the simulation in the desired Dynawo launcher

    iidm_file = list(input_dir.glob("*.*iidm"))[0]
    # We obtain the output folder path
    # and copy the input file there
    shutil.copy2(iidm_file, output_dir)

    # Run the simulation on the specified dynawo launcher
    subprocess.run(
        str(dynawo_launcher)
        + " launch --network "
        + str(output_dir / iidm_file.name)
        + " --config "
        + str(config_file)
        + " --contingencies "
        + str(contng_file)
        + " --nsa",
        shell=True,
        check=True,
    )
