
# Instructions for running the pipeline

## Prepare the basecase

0. Make sure that all the necessary files for running both simulators have 
already been prepared, with their corresponding format and directory structure.

## Setting up the virtual environment

1. Run the provided script build_and_install.sh located inside the src directory. 
This will automatically create the virtual environment and install all the 
packages necessary to use the tool. The script can also be re-run at any time 
in order to update all packages.

2. Activate the virtual environment you just created with the previous script: 
`source /path/to/the/virtual/environment/bin/activate`

## Run the pipeline

3. Now everything should be ready to run the pipeline in the active virtual environment 
with the command `run_contingencies_screening`. This provides us with several options mentioned below:
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

### input_dir (required)

The directory that contains the input case files to be used. Either as an absolute path, or a relative one.

### output_dir (required)

The directory that will store the execution results. Either as an absolute path, or a relative one.

### hades_launcher (required)

Hades executable to be used for the Hades simulations. Either use an absolute path to the executable,
or make sure it is on your $PATH.

### dynawo_launcher (required)

Dynawo executable to be used for the Dynawo simulations. Either use an absolute path to the executable,
or make sure it is on your $PATH.

### -t, --tap_changers

Enable the activation of tap changers during the simulation of the contingencies.

### -a, --replay_hades_obo

Enable the replay one by one of the most interesting N_REPLAY contingencies with the Hades simulator.

### -d, --replay_dynawo

Enable the replay of the most interesting N_REPLAY contingencies with the Dynawo simulator.

### -n N_REPLAY, --n_replay N_REPLAY (default value: 25)

Set the number for the top N contingencies to be replayed.

### -s SCORE_TYPE, --score_type SCORE_TYPE (default value: 1)

Define the type of scoring used in the ranking. Possible values are: 
[(1 = human made, 2 = machine learning)]

### -b DYNAMIC_DATABASE, --dynamic_database DYNAMIC_DATABASE

Path for a custom Dynawo model database to be used in the Dynawo simulations. 

### -m, --multithreading

Enable multithreading executions for the Hades simulations.

### -c, --calc_contingencies

Enable the usage of input files that have the contingencies calculated previously (path of output from another execution).

### -z, --compress_results

Enable the automatic cleaning of all unnecessary data generated from the Dynawo simulations and 
the compression of the output folder to a tar.gz file.

## Usage

The input directory must follow the defined structure below:

```
data/
└── 2023
    └── 01
        └── 02
            ├── unique_name_1
            │   ├── donneesEntreeHADES2_ANALYSE_SECU.xml
            │   └── recollement-auto-20230102-0000-enrichi.xiidm
            └── unique_name_2
                ├── donneesEntreeHADES2_ANALYSE_SECU.xml
                └── recollement-auto-20230102-0100-enrichi.xiidm
```
                
Under the main directory, the folders represent the years, months, and days of the snapshots, and there can be as many as desired at each level.

If you choose to reuse previously calculated contingencies (-c option), the files must come from a previous run of this same pipeline, and you should provide the overall resulting folder, not only a specific part.

When using the compression option to save space, a significant number of unnecessary files for the analysis will inevitably be deleted.

The following line provides an example of usage:
```
run_contingencies_screening -z -d -n -1 -s 2 -b dyndb -m data Results_no_taps hades2-V6.9.0.2/hades2.sh dynaflow-launcher_master_DynaflowLauncher_master_Release/dynaflow-launcher/dynaflow-launcher.sh
```

