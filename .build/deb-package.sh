#!/bin/bash
set -e

# Define package name and directory structure
PACKAGE_NAME="coretex"
PACKAGE_DIR="${PACKAGE_NAME}"
DEBIAN_DIR="${PACKAGE_DIR}/DEBIAN"
BIN_DIR="${PACKAGE_DIR}/usr/local/bin"

# Create the necessary directory structure
mkdir -p "${DEBIAN_DIR}"
mkdir -p "${BIN_DIR}"

# Create a Python virtual environment
python -m venv compile_env

# Activate the virtual environment
source compile_env/bin/activate

# Install the toml package (for generate_control.py)
pip install toml

# Move the entire dist/main directory contents directly to /usr/local/bin
mv dist/coretex/* "${BIN_DIR}/"

# Generate the control file using Python (assuming you have the Python script ready)
python generate_control.py

# Deactivate and remove the virtual environment
deactivate
rm -rf compile_env

# Build the .deb package
dpkg-deb --build "${PACKAGE_DIR}"

# Remove unnecessary dir's
rm -rf $DEBIAN_DIR
rm -rf "${PACKAGE_DIR}/usr"
