#!/bin/bash
set -e

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' ../pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Define package name and directory structure
PACKAGE_NAME="coretex"
PAYLOAD_DIR="dist/coretex/"

# Build the .pkg package using pkgbuild
pkgbuild --root "${PAYLOAD_DIR}" --identifier ai.coretex --version "${VERSION}" --install-location "/usr/local/bin" "${PACKAGE_NAME}.pkg"

# Clean up
rm -rf coretex/
rm -rf dist/