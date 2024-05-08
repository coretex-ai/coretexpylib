#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional

import click

from ..modules import ui, project_utils, utils, user
from ...entities import Project, ProjectVisibility
from ...networking import RequestFailedError
from ...configuration import loadConfig


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--type", "-t", "projectType", type = int, help = "Project type")
@click.option("--description", "-d", type = str, help = "Project description")
def create(name: Optional[str], projectType: Optional[int], description: Optional[str]) -> None:
    project = project_utils.createProject(name, projectType, description)

    selectNewProject = ui.clickPrompt("Do you want to select the new project as default? (Y/n)", type = bool, default = True)
    if selectNewProject:
        project_utils.selectProject(project.id)
        ui.successEcho(f"Project \"{project.name}\" successfully selected.")


@click.command()
@click.option("--project", "-p", type = str, help = "Project name")
@click.option("--name", "-n", type = str, help = "New Project name")
@click.option("--description", "-d", type = str, help = "New Project description")
def edit(project: Optional[str], name: Optional[str], description: Optional[str]) -> None:
    config = loadConfig()
    defaultProjectId = config.get("projectId")
    if defaultProjectId is None and project is None:
        ui.errorEcho(f"To use edit command you need to specifiy project name using \"--project\" or \"-p\" flag, or you can select default project using \"coretex project select\" command.")
        return

    if project is None and defaultProjectId is not None:
        selectedProject = Project.fetchById(defaultProjectId)
    else:
        selectedProject = Project.fetchOne(name = project)

    if name is None:
        name = ui.clickPrompt("Please enter new name for your project", type = str, default = selectedProject.name)

    if description is None:
        description = ui.clickPrompt("Please enter new description for your project", type = str, default = selectedProject.description, show_default = False)

    try:
        selectedProject.update(name = selectedProject.name, description = description)
        selectedProject.updateVisibility(ProjectVisibility.private)
        ui.successEcho(f"Project id \"{selectedProject.id}\" successfully edited.")

    except RequestFailedError:
        raise click.ClickException(f"Failed to edit project \"{selectedProject.name}\".")


@click.command()
@click.argument("name", type = str)
def select(name: str) -> None:
    project: Optional[Project] = None

    ui.progressEcho("Validating project...")

    try:
        project = Project.fetchOne(name = name)
        ui.successEcho(f"Project \"{name}\" selected successfully!")
        project_utils.selectProject(project.id)
    except ValueError:
        ui.errorEcho(f"Project \"{name}\" not found.")
        project = project_utils.promptProjectCreate("Do you want to create a project with that name?", name)
        if project is None:
            return

        project_utils.selectProject(project.id)


@click.group()
@utils.onBeforeCommandExecute(user.initializeUserSession)
def project() -> None:
    pass


project.add_command(create, "create")
project.add_command(edit, "edit")
project.add_command(select, "select")
