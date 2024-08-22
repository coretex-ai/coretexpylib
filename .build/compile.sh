#!/bin/bash
set -e

# Create a Python virtual environment
python -m venv compile_env

# Activate the virtual environment
source compile_env/bin/activate

# Install the current package and pyinstaller
pip install .. toml pyinstaller

# Run PyInstaller with the specified options
pyinstaller ../main.py --onedir --name coretex --copy-metadata readchar --copy-metadata coretex --add-data "../coretex/resources/_coretex.py:coretex/resources" --workpath coretex --noconfirm

# Deactivate and remove the virtual environment
deactivate
rm -rf compile_env
