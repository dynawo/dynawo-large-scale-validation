
Contingencies Screening
=================

A repository of scripts and utilities used for the RTE-AIA Contingencies Screening project.

***(c) 2023 Grupo AIA***

-------------------------------------------------------------------------------

## Introduction

This repository contains the required scripts of the pipeline for running the systematic 
analysis in the Hades simulator on a set of contingencies and compute their corresponding 
metrics to evaluate their severity and impact, and have them all ranked on that basis.
Once the ranking has been completed, the desired number of the most severe contingencies
can be re-run either with the Hades simulaton tool, the Dynawo simulation tool, or both of
them, in order to get the full contingency simulation for further analysis.

## Repository structure

At a high-level, this repo is structured as follows:

```
contingencies-screening/
└── src
    └── dynawo_contingencies_screening
        ├── analyze_loadflow
        ├── commons
        ├── doc
        ├── prepare_basecase
        ├── run_dynawo
        └── run_loadflow
```

[comment]: <> (tree view obtained with: tree -d -L 3 contingencies-screening)

## How to use it

The main pipeline can be used by running the command run_contingencies_screening with the required
arguments in the command line after installing and activating the provided virtual environment. 
For more information, please consult the
[Tutorial](src/dynawo_contingencies_screening/doc/Tutorial.md)
under the general doc folder.
