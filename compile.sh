#!/bin/bash

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

# Install the current package and pyinstaller
pip install .
pip install toml
pip install pyinstaller

# Run PyInstaller with the specified options
pyinstaller main.py --onedir --name coretex --copy-metadata readchar --copy-metadata coretex --add-data "coretex/resources/_coretex.py:coretex/resources" --workpath coretex --noconfirm

# Move the entire dist/main directory contents directly to /usr/local/bin
mv dist/coretex/* "${BIN_DIR}/"

# Generate the control file using Python (assuming you have the Python script ready)
python generate_control.py

# Deactivate and remove the virtual environment
deactivate
rm -rf compile_env

# Create the post-installation script to create a symlink
echo "#!/bin/bash
ln -s /usr/local/bin/coretex /usr/local/bin/coretex" > "${DEBIAN_DIR}/postinst"
chmod 755 "${DEBIAN_DIR}/postinst"

# Build the .deb package
dpkg-deb --build "${PACKAGE_DIR}"

# Remove unnecessary dir's
rm -rf $DEBIAN_DIR
rm -rf "${PACKAGE_DIR}/usr"
