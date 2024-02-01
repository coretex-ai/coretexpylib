from typing import Optional

import click

from ..modules.utils import arrowPrompt
from ... import Project, ProjectType
from ...networking import NetworkRequestError
from ...configuration import loadConfig, saveConfig


def selectProject(projectId: int) -> None:
    config = loadConfig()
    config["projectId"] = projectId
    saveConfig(config)


def selectProjectType() -> ProjectType:
    availableProjectTypes = {
        "Computer Vision": ProjectType.computerVision,
        "Motion Recognition": ProjectType.motionRecognition,
        "Bioinformatics": ProjectType.bioInformatics,
        "Other": ProjectType.other
    }

    choices = list(availableProjectTypes.keys())

    click.echo("Specify type of project that you wish to create")
    selectedChoice = arrowPrompt(choices)

    selectedProjectType = availableProjectTypes[selectedChoice]
    click.echo(f"You've chosen: {selectedChoice}")
    return selectedProjectType


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--id", type = int, help = "Project ID")
def select(name: Optional[str], id: Optional[int]) -> None:
    if name is None and id is None:
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    if name is not None:
        click.echo("Validating project...")
        try:
            project = Project.fetchOne(name = name)
            click.echo(f"Project \"{name}\" selected successfully!")
            selectProject(project.id)
        except ValueError:
            click.echo(f"Could not find project with name \"{name}\"", err = True)
            if click.confirm("Do you want to create a project with that name?", default = True):
                selectedProjectType = selectProjectType()
                newProject = Project.createProject(name, selectedProjectType)

                click.echo(f"Project with name \"{name}\" successfully created and selected.")
                selectProject(newProject.id)

    if id is not None:
        click.echo ("Validating project...")
        try:
            project = Project.fetchById(id)
            click.echo(f"Project with id \"{id}\" fetched successfully. Project name \"{project.name}\"")
            selectProject(project.id)
        except NetworkRequestError:
            click.echo(f"Failed to fetch project with provided id \"{id}\"")


@click.group()
def project() -> None:
    pass


project.add_command(select, "select")
