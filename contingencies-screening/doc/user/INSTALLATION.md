
# Instructions for installing the Contingency Screening software

This software is fully written in Python, designed to be installed as a standard Python
package using `pip` under a Python virtual environment.  However, it also needs Hades 2
(RTE's static powerflow) and DynaFlow launcher.

The steps to install the whole system, in outline form:

  * Install Hades 2 and DynaFlow launcher
  
  * Install the Operating System requirements (a basic Python system)
  
  * Create a Python virtual environment
  
  * Install the package under the Python virtual environment

The last two steps are automated with a utility script provided at the root of the
repository.

We now explain each step in more detail.



## Install Hades 2 and DynaFlow Launcher

You will need recent versions of both Hades 2 and DynaFlow Launcher.  During the
development of this project we used the following versions:

  * **DynaFlow Launcher 1.6.0 (rev:HEAD-ba79a09)**  
    Received July 2023, file
    `dynaflow-launcher_master_DynaflowLauncher_master_Release.tar.xz`

  * **Hades 2 V6.9.0.2**  
    Received July 2023, file
    `modeles_statiques_freeware_hades2_hades2-V6.9.0.2-linux.tar.gz`  
    We also used a debug version, file
    `modeles_statiques_freeware_hades2_hades2-V6.9.0.2-linux-debug.tar.gz`

You can either have their respective launchers accessible through your $PATH, or provide
the full path when you use the screening/training pipeline, it's your choice (although
having them set up in your $PATH will make for much shorter command-line invocation).



## Install the Operating System requirements

We only need a basic Python system (version 3.9 and higher), so that we can later create
the Python virtual environment under a non-root account.

If you are on Debian, Ubuntu, or any other Debian derivative, this means making sure
that you have packages python3-minimal, python3-venv, and python3-pip:

```
apt install python3-minimal python3-venv python3-pip
```

Verify that you have a Python version 3.9 or higher, by running:
```
python --version
```



## Setting up the virtual environment

Before we move on, note that you can achieve all of the following steps, including those
in the next section (package installation), by simply running the utility shell script
**`build_and_install.sh`** found in the root of the repository.

The steps are as follows.

  * Create a venv:  
	`python3 -m venv /path/to/new/virtual/environment`

  * Activate this venv:  
	`source /path/to/new/virtual/environment/bin/activate`  
    Note how the console prompt changes: you should now see the name of your virtual
    environment in parentheses, before your usual command line prompt.

  * Upgrade pip (always do this before installing anything in your venv):  
	`pip install --upgrade pip`

Other aspects to consider:
  - To deactivate the virtual environment: run `deactivate`
  - To remove the virtual environment: `rm -rf /path/to/new/virtual/environment`



## Install the package under the Python virtual environment

Again, remember that all of the steps shown below are performed automatically when using
the script **`build_and_install.sh`** found in the root of the repository. It will
automatically create the venv and install all the necessary packages to use the
tool. The script can also be re-run at any time in order to update all packages in the
venv.

Anyway, for the benefit of developers, we make these steps explicit here:

  0. You first need to install pip & friends in your venv:  
     `pip install --upgrade pip wheel setuptools build`  
     (Note 1: it's important to upgrade `pip`, since the version installed in the
     Operating System is likely to be too old.)  
     (Note 2: with more recent versions of `build`, it is redundant to explicitly
     require the installation of `wheel` and `setuptools`.)

  1. Clone the repo and move to contingencies-screening branch:
	 `git clone https://github.com/dynawo/dynawo-large-scale-validation`  
     `git checkout contingencies-screening`

  2. Build the Python package (from the main directory of the package):
	 `python -m build`

  3. Install the package:
	 `pip install dist/dynawo_contingencies_screening-0.0.1-py3-none-any.whl`


Now everything should be ready to run the software in the active virtual environment.
Test that the installation was successful by invoking the command
`run_contingencies_screening` with the help option.  You should obtain the following
output:

```
user@host$ run_contingencies_screening -h

usage: run_contingencies_screening [-h] [-t] [-a] [-d REPLAY_DYNAWO] [-n N_REPLAY] [-s SCORE_TYPE] [-b DYNAMIC_DATABASE] [-m] [-c] [-z] [-l MODEL_PATH] input_dir output_dir hades_launcher

positional arguments:
  input_dir             enter the path to the folder containing the case files
  output_dir            enter the path to the output folder
  hades_launcher        define the Hades launcher

options:
  -h, --help            show this help message and exit
  -t, --tap_changers    run the simulations with activated tap changers
  -a, --replay_hades_obo
                        replay the most interesting contingencies with Hades one by one
  -d REPLAY_DYNAWO, --replay_dynawo REPLAY_DYNAWO
                        replay the most interesting contingencies with Dynawo. Define the Dynaflow launcher.
  -n N_REPLAY, --n_replay N_REPLAY
                        define the number of most interesting contingencies to replay (default = 25)
  -s SCORE_TYPE, --score_type SCORE_TYPE
                        define the type of scoring used in the ranking (1 = human made, 2 = machine learning)
  -b DYNAMIC_DATABASE, --dynamic_database DYNAMIC_DATABASE
                        path to use a standalone dynamic database when running Dynawo
  -m, --multithreading  enable multithreading executions
  -c, --calc_contingencies
                        define the input folder that have the contingencies calculated previously (path of output from another execution)
  -z, --compress_results
                        clean and compress the results
  -l MODEL_PATH, --model_path MODEL_PATH
                        define manually the path to the model that you want to use to make the predictions.

```
