
Contingencies Screening
=======================

A repository of scripts and utilities used for the RTE-AIA Contingencies Screening
project.

***(c) 2023 Grupo AIA for RTE***

-------------------------------------------------------------------------------

## Overview

The Contingency Screening project aims to come up with a fast way to select, out of the
results of a standard powerflow-based Security Analysis, those contingencies that are
deemed "suspect" of being inexact and therefore should be run under a more sophisticated
powerflow that takes into account (albeit in an approximate way) the _dynamics_ of the
network---especially the effect of controls, with their temporal characteristics.

This repository contains Python software to address this problem. It is designed to use
**Hades** (version 2) as the static powerflow engine, and **DynaFlow** as a modern
dynamics-based powerflow. The approach is based on "supervised learning", although not
in the customary model-blind, machine-learning kind of way, but guided by engineering
knowledge and trying to obtain interpretable models. The overall idea is to run both
Hades and DynaFlow for the full list of contingencies over a large set of snapshots and
compare the results by means of a suitably-defined metric (i.e., a distance function);
this metric then becomes the target to predict, based on a suitable set of predictor
variables that we can extract from Hades results. The predictive model can be obtained
by different means. The software currently implements two modeling approaches:

  * A human-interpretable model, using median-based linear regression. This model is
    quite transparent to domain experts, as one can directly see the relative weights of
    each predictor variable. Modifications and tweaks can be done directly, too. For
    instance, if an expert judges that certain variable should _not_ have any influence
    but appears in the regression with some weight (which may happen when the
    regression overfits to the data), its weight may be manually set to zero in the
    model.

  * A Gradient Boosting model, using GBM. This model is more of a black-box, although
    one may probe for variable importance using techniques such as SHAP values (with all
    their limitations, since these only provide instance-local explanation, not a global
    one). The advantage is that this model provides better predictive performance.


Training is a very slow process, since one needs to perform many Hades and DynaFlow
calculations, plus the reduction of DynaFlow results to Hades-compatible variables (to
be able to compare them), plus model training proper.  However, once the models are
obtained, it is very fast to predict a score with them, which is the final goal
here. Thanks to a fast screening, one can get the best out of both powerflow methods:
the static powerflow, which is very fast, is first used to run the bulk of all
contingencies; then the more exact (but slower) dynamic powerflow is used to verify only
the screened ones.

The software in this repository is therefore used in two modes:

  * **Model Training:** this will be done occasionally, once every few weeks (or
    months), to retrain the model in order to prevent data drift / model drift.

  * **Screening:** this can be done on every Security Analysis. After all contingencies
  have been calculated with the Hades SA, the software obtains their predicted score
  (model evaluation) and they are then ranked. Those above a chosen threshold (i.e.,
  those that the model predicts to be more different) can be re-run using DynaFlow.

There are also companion Notebooks for the analysis and exploration of results.



## Project structure

At a high-level, this repository is structured as follows:

[comment]: <> (tree view obtained with: tree -d -L 3 contingencies-screening)
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



## Documentation

The documentation is located under the `doc` folder. The main contents are:

  * [USAGE](doc/user/USAGE.md): covers the installation of
    the Python package and usage of the main components, `run_contingencies_screening`
    (the main screening pipeline) and `train_test_loadflow_results` (for training
    models).

  * [ANALYSIS](doc/user/ANALYSIS.md): covers how to
    prepare the cases and use the Jupyter notebooks for analyzing results, both global
    (model performance, contingency rankings, etc.) and individual (exploring the result
    of a particular contingency case).

  * [SUMMARY_CONCLUSIONS](doc/user/SUMMARY_CONCLUSIONS.md):
    offers general conclusions we have drawn from the modeling results obtained on the
    January+February+June 2023 dataset (see also the paper to be submitted soon).

