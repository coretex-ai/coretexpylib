from typing import Optional

import click

from .utils import readConfig, saveConfig
from .. import Project


def promptSelect() -> None:
    click.echo("No project selected")
    projectName = click.prompt("Enter project name", type = int)

    projects = Project.fetchAll(name = projectName, include_sessions = 1)
    if len(projects) > 0:
        select(id = projects[0].id)
        return

    click.echo("Could not find poject")
    if not click.prompt("Do you want to create a project by that name?", type = bool, default = True):
        return

    newProject = Project.createProject(projectName, 8)
    if newProject is not None:
        select(id = newProject.id)
        return

    click.echo("Failed to create project")


click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--id", type = int, help = "Project ID")
def select(name: Optional[str], id: Optional[int]) -> None:
    if not (name ^ id):
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    if name is not None:
        click.echo("Checking project name")

        projects = Project.fetchAll(name = name, include_sessions = 1)
        if len(projects) == 0:
            click.echo("Could not find project by that name", err = True)
            return

        id = projects[0].id

    config = readConfig()
    config["projectId"] = id
    saveConfig(config)


@click.group()
def project() -> None:
    pass


project.add_command(select,"select")
