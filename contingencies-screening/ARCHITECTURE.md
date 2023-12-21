
Contingencies Screening
=================

A repository of scripts and utilities used for the RTE-AIA Contingencies Screening project.

***(c) 2023 Grupo AIA***

-------------------------------------------------------------------------------

## Introduction

This repository contains the necessary scripts of the pipeline for running a systematic/security analysis within the Hades simulator. The analysis involves running simulations on a set of contingencies and calculating their respective metrics to assess the extent of divergence compared to a dynamic simulator, in this case Dynawo. The results are then ranked based on this comparison.

After the ranking process is completed, the user can selectively re-run the most critical contingencies (those that are believed to be more different) using either the Hades simulation tool, the Dynawo simulation tool, or both. This step aims to generate comprehensive contingency simulations for in-depth analysis, facilitating the identification and exploration of discrepancies between the two simulation tools.

This approach is particularly valuable for executing a substantial number of contingencies using loadflow, which is a more efficient process. Subsequently, it reexecutes only those that 
can give a different result with dynamic simulation, achieving a higher degree of precision.

At a high-level, this repo is structured as follows:

```
contingencies-screening/
└── src
    └── dynawo_contingencies_screening
        ├── analyze_loadflow
        ├── commons
        ├── doc
        ├── notebook_analisis
        ├── prepare_basecase
        ├── run_dynawo
        └── run_loadflow
```

[comment]: <> (tree view obtained with: tree -d -L 3 contingencies-screening)

## How to use it

The main pipeline can be used by running the command run_contingencies_screening with the required arguments in the command line after installing and activating the provided virtual environment. For more information about how to install it, please consult the [USAGE](src/dynawo_contingencies_screening/doc/USAGE.md) under the general doc folder.

## Results
To see how to prepare the cases and use the jupyter notebook for analyzing results, go to the following file: [ANALYSIS](src/dynawo_contingencies_screening/doc/ANALYSIS.md)
The general conclusions of the results and the models used can be found in the [SUMMARY_CONCLUSIONS](src/dynawo_contingencies_screening/doc/SUMMARY_CONCLUSIONS.md) document, or by reading the published paper related to this development.

