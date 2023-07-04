
# Instructions for running the pipeline

## Prepare the basecase

0. Make sure that all the necessary files for running both the simulators have 
already been prepared, with their corresponding format and directory structure.

## Setting up the virtual environment

1. Run the provided script build_and_install.sh located inside the src directory. 
This will automatically create the virtual environment and install all the 
packages necessary to use the tool. The script can also be re-run at any time 
in order to update all packages.


2. Activate the virtual environment you just created with the previous script: 
`source /path/to/the/virtual/environment/bin/activate`

## Run the pipeline

3. Now everything should be ready to run the pipeline with the virtual environment 
activated through the command line with the command run_contingencies_screening.
This provides us with several options mentioned below:

        usage: run_contingencies_screening [-h] [-t] [-a] [-d] [-n N_REPLAY] input_dir output_dir hades_launcher dynawo_launcher

        positional arguments:
          input_dir             enter the path to the folder containing the case files
          output_dir            enter the path to the folder containing the case files
          hades_launcher        define the Hades launcher
          dynawo_launcher       define the Dynawo launcher
        
        options:
          -h, --help            show this help message and exit
          -t, --tap_changers    run the simulations with activated tap changers
          -a, --replay_hades    replay the worst contingencies with Hades
          -d, --replay_dynawo   replay the worst contingencies with Dynawo
          -n N_REPLAY, --n_replay N_REPLAY
                                define the number of worst contingencies to replay (FROM, TO, BOTH)
          -s SCORE_TYPE, --score_type SCORE_TYPE
                        Define the type of scoring used in the ranking (1 = discrete human made, 2 = continuous human made, 3 = machine learning disc, 4 = machine learning cont
          -b DYNAMIC_DATABASE, --dynamic_database DYNAMIC_DATABASE
                        Path to obtain a different dynamic database when using Dynawo


### input_dir (required)

The directory that contains the BASECASE. Either as an absolute path, or a relative one.

### output_dir (required)

The directory that will store the results, either as an absolute path, or a relative one.

### hades_launcher (required)

Hades executable to be used for the Hades simulations. Either use an absolute path to the executable,
or make sure it is on your $PATH.

### dynawo_launcher (required)

Dynawo executable to be used for the Dynawo simulations. Either use an absolute path to the executable,
or make sure it is on your $PATH.

### -t, --tap_changers

Enable the activation of tap changers in the simulation of the contingencies.

### -a, --replay_hades

Enable the replay of the top N_REPLAY worst contingencies with Hades simulator.

### -d, --replay_dynawo

Enable the replay of the top N_REPLAY worst contingencies with Dynawo simulator.

### -n N_REPLAY, --n_replay N_REPLAY (default value: 25)

Set the number for the top X contingencies to be replayed.

### -s, --score_type

Define the type of scoring used in the ranking. Possible values are: 
[1 (discrete human made), 2 (continuous human made), 3 (machine learning discrete), 4 (machine learning continuous)]

### -d, --dynamic_database

Path for a custom Dynamo model database to be used in the Dynawo simulations. 