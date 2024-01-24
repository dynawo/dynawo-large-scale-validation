
# Overview

As explained in the project's [README](README.md), this software has two modes
of usage:

  a) the _screening_ mode, where for each contingency calculated by Hades 2
  Security Analysis, we produce a score that predicts how different the results
  are expected to be, compared to DynaFlow's.
  
  b) the _model-training_ mode, in which we run both Hades and DynaFlow on a
  large set of snapshots and contingency lists to obtain predictive models via
  various supervised learning techniques (linear regression and gradient
  boosting).




# Instructions for running the screening pipeline

## Preparing the input

The input directory can be freely structured, as long as each snapshot is
contained in its own directory, containing both the Hades and the DynaFlow
input.  This is a typical example:

```
data/
└── 2023
    └── 01
        └── 02
            ├── unique_snapshot_name_1
            │   ├── donneesEntreeHADES2_ANALYSE_SECU.xml
            │   └── recollement-auto-20230102-0000-enrichi.xiidm
            ...
            └── unique_snapshot_name_N
                ├── donneesEntreeHADES2_ANALYSE_SECU.xml
                └── recollement-auto-20230102-xxxx-enrichi.xiidm
```
                
Under the main directory, these folders represent the years, months, and days of
the snapshots, and there can be as many as desired at each level. It is not
strictly necessary to organize the folders using these names (in fact, any
directory tree will be traversed), but it is useful for keeping things
organized.  What is very important is that each snapshot has its own unique
folder, and to name the files according to the patterns
`donneesEntreeHADES2*.xml` (for Hades 2) and `*.*iidm` (for DynaFlow).

In addition, one would typically provide a specific database of dynamic models
to override Dynawo's default ones (see option `-b`).  When providing this, the
database should be provided as follows:

```
dyndb_folder_name
├── assembling.xml
└── setting.xml
```

In this case the folder name and its location is free to choose, but these two
file names must be respected in their entirety



## Running the pipeline

Make sure to have activated the Python virtual environment in which you have
installed the software: `source /path/to/the/virtual/environment/bin/activate`

The pipeline is run using  the command `run_contingencies_screening`:
```
usage: run_contingencies_screening [-h] [-t] [-a] [-d] [-n N_REPLAY] [-s SCORE_TYPE] [-b DYNAMIC_DATABASE] [-m] [-c] [-z] input_dir output_dir hades_launcher dynawo_launcher

positional arguments:
  input_dir             enter the path to the folder containing the case files
  output_dir            enter the path to the output folder
  hades_launcher        define the Hades launcher
  dynawo_launcher       define the Dynawo launcher

options:
  -h, --help            show this help message and exit
  -t, --tap_changers    run the simulations with activated tap changers
  -a, --replay_hades_obo
                        replay the most interesting contingencies with Hades one by one
  -d, --replay_dynawo   replay the most interesting contingencies with Dynawo
  -n N_REPLAY, --n_replay N_REPLAY
                        define the number of most interesting contingencies to replay (default = 25)
  -s SCORE_TYPE, --score_type SCORE_TYPE
                        define the type of scoring used in the ranking (1 = human made, 2 = machine learning)
  -b DYNAMIC_DATABASE, --dynamic_database DYNAMIC_DATABASE
                        path to use a standalone dynamic database when running Dynawo
  -m, --multithreading  enable multithreading executions in Hades
  -c, --calc_contingencies
                        define the input folder that have the contingencies calculated previously
  -z, --compress_results
                        clean and compress the results
```

Let us now see these options in detail.


### input_dir (required)

The directory that contains the snapshot files to be used. Either as an absolute
path, or a relative one. See the previous section on how the input files should
be named and structured in folders.

### output_dir (required)

The directory that will store the execution results. Either as an absolute path,
or a relative one. The output tree structure will reflect the same structure as
the input_dir.

### hades_launcher (required)

Hades executable to be used for the Hades simulations. Either use an absolute
path to the executable, or make sure it is on your $PATH.

### dynawo_launcher (required)

Dynawo executable to be used for the Dynawo simulations. Either use an absolute
path to the executable, or make sure it is on your $PATH.

### -t, --tap_changers

Enable the activation of tap changers during the calculation of contingencies in
Hades 2 SA.

### -a, --replay_hades_obo

Enable the replay _one by one_ of the most interesting `N_REPLAY` contingencies
with the Hades 2 simulator. This option was introduced only because when Hades 2
runs a _SA session_, it takes some "shortcuts" that are not normally done when
running one single case explicitly, as an ordinary powerflow. What this option
does is preparing individual Hades input files and run them individually in this
manner, in order to explore whether the results change or not with respect to
the SA session. It does so only for the top N contingencies in the ranking
obtained via the model predictions.

### -d, --replay_dynawo

Enable the replay of the most interesting `N_REPLAY` contingencies with the
DynaFlow simulator. What this option does is, in combination with the `-n`
option, run the (predicted) top N most different contingencies using DynaFlow
Launcher, in order to calculate their actual score (i.e. the actual value of the
metric that measures the "distance" between Hades and DynaFlow results). These
actual scores are then _added_ to the results dataframe. This allows one to
check how well (or badly) the prediction is working.

### -n N_REPLAY, --n_replay N_REPLAY (default value: 25)

Set the number for the top N contingencies to be replayed.  
**IMPORTANT:** This option is used with the "magic" value **-1** when we want to
generate a dataset for training models. What it does in this case is running
**all** contingencies under DynaFlow as well as Hades, so that thee resulting
dataframe contains the actual score (in the last column), that is, the target
variable for the predictive model training stage. This output dataframe is
therefore the input for the training script (see the last section below).

### -s SCORE_TYPE, --score_type SCORE_TYPE (default value: 1)

Define the type of scoring used in the ranking. Possible values are: 
[(1 = human-explicable, 2 = machine learning)]

### -b DYNAMIC_DATABASE, --dynamic_database DYNAMIC_DATABASE

Path for a custom Dynawo model database to be used in the DynaFlow
simulations. This directory _must_ contain a file named `assembling.xml` and
another named `setting.xml`.

### -m, --multithreading

Enable multithreaded execution for the Hades 2 runs.

### -c, --calc_contingencies

Enable the usage of input files that have their contingencies already calculated
previously (i.e., the path of the output from another execution).

### -z, --compress_results

Enable the automatic cleaning of all unnecessary data generated from the
DynaFlow simulations, and compress the output folder to a `tar.gz` file.




# Instructions for running the model-training command

Models can degrade in performance, in what is called model drift / data
drift. For instance, the network scenarios may start to change and become more
stressed in some areas and less in others, compared to the ones used in the
previous train cycle (this would be an example of data drift). Or, changes in
either Hades or DynaFlow Launcher (or Dynawo models) could result in significant new
differences in what they calculate (this would be an example of model drift).
Therefore it may be necessary to re-train the predictive models once in a while.

With the current software, this is done in two stages: first, one must produce a
new dataset of "ground truth" data, that is, a large data set of Hades and
DynaFlow executions with their actual scoring (their distance). Second, one must
perform the model training (regression, etc.) on that dataset.



## Preparing a new train dataset

Before running the train script, one should prepare (calculate) the new training
dataset. This consists in running all contingencies (for all available
snapshots), both in Hades2 SA and in DynaFlow. For example, right now the model
is trained with ~1,500 snapshots (with approximately 400 contingencies each),
corresponding to almost three months: January, February, and June 2023.  This
took about 2 months to calculate on a powerful server!

The command to launch this is actually the same as the one used for running the
screening pipeline, except that one should use the options **`-d -n -1`**:

```
run_contingencies_screening -t -d -n -1 -b ../dyndb input_dir output_dir
hades_launcher dynawo_launcher
```

This will execute, both with Hades and Dynawo, _all_ the contingencies
configured in the input snapshots.



## Train the new model

The train script will produce the new models (LR, GBM). These consist
in one file each, one in “pickle” format (GBM) and one in readable JSON format
(LR).

Run the train process by launching the following command line:

```
train_test_loadflow_results ./massive_execution_output_folder ./folder_where_to_save_models
```

where `massive_execution_output_folder` is the output folder from the previous
execution.



## Using the newly trained models for screening

**TODO:** currently, the newly created models should be copied to the Python source,
following this manual procedure. This should be managed through configurable
user directories instead.

  1. Rename the `GBR_model.pkl` file to `ML_taps.pkl` or `ML_no_taps.pkl` and
     then copy it to the package folder
     `src/dynawo_contingencies_screening/analyze_loadflow/`, inside the Python
     sources.

  2. Perform the same action for the `LR_median.json` file, renaming it to
     `LR_taps.json` or `LR_no_taps.json`.

  3. Reinstall the Python package as in the INSTALLATION instructions.

