
# Instructions for execution/development requirements

## OS, development software and utilities

- Install base OS: Debian 11 (from netinst). Standard Gnome desktop and ssh.

- Install Python 3: 

	- sudo apt-get update && sudo apt-get upgrade

	- sudo apt-get install python3.9

- Install pip and venv: sudo apt install python3-venv python3-pip

- Install Jupyter and some other python debs for DS: apt-get install jupyter python-numpy python3-numpy

- Only for development:

	- Install a python IDE. (for ex. PyCharm: https://www.jetbrains.com/help/pycharm/installation-guide.html#requirements)

	- Install python development utilities: apt-get install black flake8 python3-pytest
	
	- Install parallel package for faster execution: sudo apt-get install parallel


## Virtual environment creation

- Create the virtual environment: python3 -m venv /path/to/new/virtual/environment

- Activate the virtual environment: source /path/to/new/virtual/environment/bin/activate

Now you should have the name of your virtual environment in parentheses before the username on the command line.

Others:

- Deactivate virtual environment: deactivate

- Remove virtual environment: rm -rf /path/to/new/virtual/environment


## Virtual environment configuration (venv must be actived to proceed)

Now, you have a self-contained directory tree that contains a Python installation for a particular version of Python, plus a number of additional packages. All the modifications that you make in this installation (with pip) will not affect the general installation of Python.

- Upgrade pip: python -m pip install --upgrade pip (we use python instead of python3 because in this environment we only have Python 3).


## Install Dynawo

- Follow the instructions of this website: https://dynawo.github.io/install/


## Install Hades

- To compare between Hades, it is assumed that you already have Hades installed in your environment.


## Install dynaflow-validation (venv must be actived to proceed)

- Install dynaflow-validation with all dependencies: pip install -i https://test.pypi.org/simple/ dynaflow-validation-RTE-AIA

(For now, to avoid problems with other packages, it is better if you download the source code from the link and install it manually with: pip install name_of_tar.gz)
	

## Jupyter Notebooks configuration

To use the virtual environment interpreter in Jupyter Notebooks, we have to do the following steps:

	1. Activate virtual environment source /path/to/new/virtual/environment/bin/activate

	2. Install ipykernel which provides the IPython kernel for Jupyter: pip install ipykernel

	3. Add your virtual environment to Jupyter: python -m ipykernel install --user --name=NAME-OF-INTERPRETER

	4. Run this two commands in order to register this extensions with jupyter: 
        	
        	jupyter nbextension enable --py widgetsnbextension
        	jupyter nbextension enable --py --sys-prefix qgrid

	5. Open Jupyter and, in Kernel Options, select your new Kernel.


## IDE configuration (only for development)
	
To use the virtual environment interpreter in our IDE we have to open our Python IDE (for example, PyCharm) and go to Interpreter Configuration (in the case of PyCharm, we have the direct option to Add Interpreter). We must choose the option that allows us to add a new interpreter and then, we only have to select the Python interpreter from the path where we have installed the Virtual Environment (in /bin directory).
