from typing import Optional

import click
from ..configuration import loadConfig, saveConfig, selectProject
from .. import Project, ProjectType


def selectProjectType() -> Optional[ProjectType]:
    for i in range(3):
        click.echo("Specify type of project that you wish to create")
        for projectType in ProjectType:
            click.echo(f"\t{projectType.name.ljust(25)} - {projectType.value}")

        choice = click.prompt("Enter the number corresponding to the project type", type=int)
        try:
            selectedProjectType = ProjectType(choice)
            click.echo(f"You've chosen: {selectedProjectType.name}")
            return selectedProjectType

        except ValueError:
            click.echo("Invalid choice. Please try again.")

    return None


def createProject(name: str) -> Optional[Project]:
    selectedProjectType = selectProjectType()
    if selectedProjectType is not None:
        try:
            newProject = Project.createProject(name, selectedProjectType)
            click.echo(f"Project with name {name} successfully created.")
            return newProject
        except:
            click.echo("Failed to create the project.")
            return None
    else:
        return None


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--id", type = int, help = "Project ID")
def select(name: Optional[str], id: Optional[int]) -> None:
    if name is None and id is None:
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    if name:
        click.echo("Checking project name")
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

    if id:
        click.echo ("Checking project id")
        try:
            project = Project.fetchById(id)
            click.echo(f"Project with id \"{id}\" fetched successfully. Project name \"{project.name}\"")
        except:
            click.echo(f"Failed to fetch project with provided id \"{id}\"")
            return

        selectProject(project.id)


@click.group()
def project() -> None:
    pass


project.add_command(select, "select")
