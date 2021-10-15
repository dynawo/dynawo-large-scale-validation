from distutils.core import setup
import os
import subprocess

setup(
    include_package_data=True,
    install_requires = [
    "lxml>=4.6.3",
    "pandas>=1.3.0",
    "plotly>=5.1.0",
    "frozendict>=2.0.3",
    "networkx>=2.5.1",
    "pyvis>=0.1.9",
    "qgrid>=1.3.1",
    "notebook>=6.4.0",
    "numpy>=1.21.0",
    "matplotlib>=3.4.2",
    "ipywidgets>=7.6.3",
    "tqdm>=4.62.1",
    "scipy>=1.6.1",
    "seaborn>=0.11.2",
    ],
    scripts=['src/dynawo_validation/dynawaltz/pipeline/dynawaltz_run_validation','src/dynawo_validation/commons/create_graph.py', 'src/dynawo_validation/commons/xml_utils/convert_dwaltz2dwoAdwoB_both.sh', 'src/dynawo_validation/commons/xml_utils/xml_format_dir.sh','src/dynawo_validation/commons/dynawo_validation_find_path', 'src/dynawo_validation/dynaflow/pipeline/dynaflow_run_validation','src/dynawo_validation/commons/create_graph.py', 'src/dynawo_validation/commons/xml_utils/convert_dflow2dwoAdwoB_both.sh', 'src/dynawo_validation/commons/xml_utils/xml_format_dir.sh', 'src/dynawo_validation/commons/dynawo_validation_extract_bus', 'src/dynawo_validation/dynawaltz/pipeline/prepare_pipeline_basecase.py',],
)
