import toml


def main() -> None:
    # Load data from pyproject.toml
    with open("pyproject.toml", "r") as f:
        pyproject = toml.load(f)

    # Extract necessary information
    packageName = pyproject['project']['name']
    version = pyproject['project']['version']
    description = pyproject['project']['description']

    # Create control file content
    controlContent = f"""
    Package: {packageName}
    Version: {version}
    Section: base
    Priority: optional
    Architecture: all
    Depends: python3
    Maintainer: Your Name <your.email@example.com>
    Description: {description}
    """

    # Write to control file
    with open(f"{packageName}/DEBIAN/control", "w") as controlFile:
        controlFile.write(controlContent)

if __name__ == "__main__":
    main()
