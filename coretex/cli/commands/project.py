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
from ..modules.ui import clickPrompt, errorEcho, successEcho, progressEcho
from ...entities import Project, ProjectType, ProjectVisibility
from ...networking import NetworkRequestError, EntityNotCreated, networkManager, RequestFailedError
from ...configuration import loadConfig


@click.command()
@click.option("--project", "-p", type = str, help = "Project name")
@click.option("--type", "-t", type = int, help = "Project type")
@click.option("--description", "-d", type = str, help = "Project description")
def create(name: Optional[str], type: Optional[int], description: Optional[str], visibility: Optional[int]) -> None:
    if name is None:
        name = clickPrompt("Please enter name of the project you want to create:", type = str)

    if type is None:
        type = project_utils.selectProjectType()

    if description is None:
        description = clickPrompt("Please enter your project's description:", type = str)

    try:
        project = Project.createProject(name, ProjectType(type), description)

        if project is not None:
            ui.successEcho(f"Project \"{name}\" created successfully.")
            selectNewProject = clickPrompt("Do you want to select new project as default? (Y/n)", type = bool, default = True)

            if selectNewProject:
                project_utils.selectProject(project.id)
                successEcho(f"Project \"{project.name}\" successfully selected.")

    except EntityNotCreated:
        raise click.ClickException(f"Failed to create project \"{name}\".")


@click.command()
@click.option("--project", "-p", type = str, help = "Project name")
@click.option("--description", "-d", type = str, help = "Project description")
def edit(name: Optional[str], description: Optional[str], visibility: Optional[int]) -> None:
    config = loadConfig()
    defaultProjectId = config.get("projectId")
    if defaultProjectId is None and name is None:
        errorEcho(f"To use edit command you need to specifiy project name using \"--project\" or \"-p\" flag, or you can select default project using \"coretex project select\" command.")

    defaultProject = Project.fetchById(config["projectId"])

    if name is None:
        selectedProject = defaultProject
    else:
        selectedProject = Project.fetchOne(name = project)

    if description is None:
        description = clickPrompt("Please enter new description for your project", type = str, default = selectedProject.description)

    try:
        selectedProject.update(name = selectedProject.name, description = description)
        response = networkManager.post("entity-visibility", {
            "entity_id": config["projectId"],
            "type": 1,  # this number represents Project Entity enum value on backend side
            "visibility": ProjectVisibility.private,
        })

        if not response.hasFailed():
            successEcho(f"Project id \"{config['projectId']}\" successfully edited.")

    except RequestFailedError:
        raise click.ClickException(f"Failed to edit project \"{selectedProject.name}\".")


@click.command()
@click.option("--project", "-p", type = str, help = "Project name")
def select(name: Optional[str], id: Optional[int]) -> None:
    if name is None and id is None:
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    project: Optional[Project] = None

    if name is not None:
        progressEcho("Validating project...")

        try:
            project = Project.fetchOne(name = name)
            successEcho(f"Project \"{name}\" selected successfully!")
            project_utils.selectProject(project.id)
        except ValueError:
            errorEcho(f"Project \"{name}\" not found.")
            project = project_utils.promptProjectCreate("Do you want to create a project with that name?", name)
            if project is None:
                return

    if id is not None:
        progressEcho("Validating project...")
        try:
            project = Project.fetchById(id)
            successEcho(f"Project with id \"{id}\" fetched successfully. Project name \"{project.name}\"")
        except NetworkRequestError:
            errorEcho(f"Failed to fetch project with provided id \"{id}\"")

    if project is not None:
        project_utils.selectProject(project.id)


@click.group()
@utils.onBeforeCommandExecute(user.initializeUserSession)
def project() -> None:
    pass


project.add_command(create, "create")
project.add_command(edit, "edit")
project.add_command(select, "select")
