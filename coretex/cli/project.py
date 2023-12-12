from typing import Optional

import click

from ..networking import NetworkRequestError
from .utils import arrowPrompt
from ..configuration import loadConfig, saveConfig
from .. import Project, ProjectType


def selectProject(projectId: int) -> None:
    config = loadConfig()
    config["projectId"] = projectId
    saveConfig(config)


def selectProjectType() -> ProjectType:
    choices = [projectType.name for projectType in ProjectType]

    click.echo("Specify type of project that you wish to create")
    selectedChoice = arrowPrompt(choices)

    selectedProjectType = ProjectType[selectedChoice]
    click.echo(f"You've chosen: {selectedProjectType.name}")
    return selectedProjectType


def createProject(name: str) -> Optional[Project]:
    selectedProjectType = selectProjectType()
    newProject = Project.createProject(name, selectedProjectType)
    click.echo(f"Project with name {name} successfully created.")
    return newProject


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

        except:
            click.echo(f"Could not find project with name \"{name}\"", err = True)
            if click.confirm("Do you want to create a project by that name?", default = True):
                newProject = createProject(name)

                if newProject is not None:
                    selectProject(newProject.id)
                    click.echo(f"Project \"{name}\" selected successfully!")
                else:
                    click.echo("Failed to select project. Please try again.")
                    return

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
