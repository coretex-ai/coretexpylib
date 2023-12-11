from typing import Optional

import click
from ..configuration import loadConfig, saveConfig
from .. import Project, ProjectType


def createProject(name: str) -> None:
    try:
        new_project = Project.createProject(name, ProjectType.other)
        if new_project is not None:
            config = loadConfig()
            config["projectId"] = new_project.id
            saveConfig(config)
    except Exception as e:
        raise click.ClickException(f"Failed to create project: {e}")


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--id", type = int, help = "Project ID")
def select(name: Optional[str], id: Optional[int]) -> None:
    if name is None and id is None:
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    if name:
        click.echo("Checking project name")
        projects = Project.fetchAll(name = name, include_sessions = 1)
        if not projects:
            click.echo(f"Could not find project with name \"{name}\"", err = True)
            if click.confirm("Do you want to create a project by that name?", default = True):
                createProject(name)
        else:
            click.echo(f"Project \"{name}\" selected successfully!")

    if id:
        click.echo("Checking project id")
        project = Project.fetchById(id)
        if project:
            click.echo(f"Project with id \"{id}\" fetched successfully. Project name \"{project.name}\"")
        else:
            click.echo(f"Failed to fetch project with provided id \"{id}\"")

    config = loadConfig()
    config["projectId"] = id
    saveConfig(config)


@click.group()
def project() -> None:
    pass


project.add_command(select, "select")
