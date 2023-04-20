import os


def run_dynaflow_basecase(input_dir, dynawo_launcher):
    # From the data specified in the input directory,
    # run the simulation in the desired Dynawo launcher
    os.system(
        dynawo_launcher
        + " jobs-with-curves "
        + input_dir / "dynawo/JOB.xml"
    )