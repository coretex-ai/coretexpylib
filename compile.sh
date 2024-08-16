#!/bin/bash

# Create a Python virtual environment
python -m venv compile_env

# Activate the virtual environment
source compile_env/bin/activate

# Install the current package and pyinstaller
pip install .
pip install pyinstaller

# Run PyInstaller with the specified options
pyinstaller main.py --onedir --copy-metadata readchar --copy-metadata coretex --add-data "coretex/resources/_coretex.py:coretex/resources"

# Deactivate and remove the virtual environment
deactivate
rm -rf compile_env

# Check that everything is fine by running the compiled program
./dist/main/main
