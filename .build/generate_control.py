import toml


def main() -> None:
    # Load data from pyproject.toml
    with open("../pyproject.toml", "r") as f:
        pyproject = toml.load(f)

    # Extract necessary information
    packageName = pyproject["project"]["name"]
    version = pyproject["project"]["version"]
    description = pyproject["project"]["description"]

    # Create control file content
    controlContent = (
        f"Package: {packageName}\n"
        f"Version: {version}\n"
        "Section: base\n"
        "Priority: optional\n"
        "Architecture: all\n"
        "Depends: python3\n"
        "Maintainer: Your Name < your.email@example.com >\n"
        f"Description: {description}\n"
    )

    # Write to control file
    with open(f"{packageName}/DEBIAN/control", "w") as controlFile:
        controlFile.write(controlContent)


if __name__ == "__main__":
    main()
