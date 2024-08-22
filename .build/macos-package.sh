#!/bin/bash
set -e

# Define package name and directory structure
PACKAGE_NAME="coretex"
PAYLOAD_DIR="dist/coretex/"

# Build the .pkg package using pkgbuild
pkgbuild --root "${PAYLOAD_DIR}" --identifier ai.coretex --version 1.0 --install-location "/usr/local/bin" "${PACKAGE_NAME}.pkg"

rm -rf coretex/
rm -rf dist/
