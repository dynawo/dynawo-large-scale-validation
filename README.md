
Dynawo validation
=================

A repository of scripts and utilities used for the RTE-AIA project. It can be used in package form or each of the scripts individually.
*"Validation of dynamic simulations made using open source tool"*.

***(c) 2023 Grupo AIA***

-------------------------------------------------------------------------------

## Intro
This repository contains a copy of the scripts in the master branch of the project, as well as a 
folder containing the required scripts to run the simulation and analyze the load-flow results. 
The pipeline of events that the scripts follow starts with the preparation of the specified basecase,
then follows the selection of the two simulators to be used and once both simulations are completed,
the resulting load-flow data is extracted, so it can be analyzed by a professional.

## Repository structure

At a high-level, this repo is structured as follows:

```
contingencies-screening/
└── src
    └── dynawo_contingencies_screening
        ├── analyze_loadflow
        ├── commons
        ├── prepare_basecase
        ├── run_dynawo
        └── run_loadflow
```

[comment]: <> (tree view obtained with: tree -d -L 3 contingencies-screening)

## How to use it
The pipeline can be used in one of two ways: Firstly, this repo can be cloned and the scripts be
used directly off their folder. Secondly, the script provided in the contingencies-screening 
folder can be executed to have all the dependencies automatically installed. The second method 
is the one recommended since it is the most convenient and automated process of the two.
For more information, please consult the
[README_INSTALLATION.md](large-scale-validation/src/dynawo_validation/doc/README_INSTALLATION.MD)
under the general doc folder.
