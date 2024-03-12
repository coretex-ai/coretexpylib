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
from ...networking import NetworkRequestError, EntityNotCreated, networkManager
from ...configuration import loadConfig, saveConfig


def selectProject(projectId: int) -> None:
    config = loadConfig()
    config["projectId"] = projectId
    saveConfig(config)


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--type", "-t", type = int, help = "Project type")
@click.option("--description", "-d", type = str, help = "Project description")
@click.option("--visibility", "-v", type = str, help = "Project visibility")
def create(name: Optional[str], type: Optional[int], description: Optional[str], visibility: Optional[int]) -> None:
    if name is None:
        name = clickPrompt("Please enter name of the project you want to create:", type = str)

    if type is None:
        type = project_utils.selectProjectType()

    if description is None:
        description = clickPrompt("Please enter your project's description:", type = str)

    if visibility is None:
        visibility = project_utils.selectProjectVisibility()

    try:
        Project.createProject(name, ProjectType(type), description, ProjectVisibility(int(visibility)))
        ui.successEcho(f"Project \"{name}\" created successfully.")
    except EntityNotCreated:
        raise click.ClickException(f"Failed to create project \"{name}\".")


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--visibility", "-v", type = int, help = "Project visibility")
@click.option("--description", "-d", type = str, help = "Project description")
def edit(name: Optional[str], description: Optional[str], visibility: Optional[int]) -> None:
    config = loadConfig()
    selectedProject = Project.fetchById(config["projectId"])

    if name is None:
        name = clickPrompt("Please enter new name for your project", type = str, default = selectedProject.name)

    if description is None:
        description = clickPrompt("Please enter new description for your project", type = str, default = selectedProject.description)

    if visibility is None:
        visibility = project_utils.selectProjectVisibility()

    try:
        selectedProject.update(name = name, description = description)
        networkManager.post("entity-visibility", {
            "entity_id": config["projectId"],
            "type": 1,
            "visibility": visibility,
            "user_ids": ["uuid"]
        })
    except NetworkRequestError:
        raise click.ClickException(f"Failed to create project \"{name}\".")


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--id", type = int, help = "Project ID")
def select(name: Optional[str], id: Optional[int]) -> None:
    if name is None and id is None:
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    project: Optional[Project] = None

    if name is not None:
        progressEcho("Validating project...")

        try:
            project = Project.fetchOne(name = name)
            successEcho(f"Project \"{name}\" selected successfully!")
            selectProject(project.id)
        except ValueError:
            errorEcho(f"Project \"{name}\" not found.")
            project = project_utils.promptProjectCreate("Do you want to create a project with that name?", name)

    if id is not None:
        progressEcho("Validating project...")
        try:
            project = Project.fetchById(id)
            successEcho(f"Project with id \"{id}\" fetched successfully. Project name \"{project.name}\"")
        except NetworkRequestError:
            errorEcho(f"Failed to fetch project with provided id \"{id}\"")

    if project is not None:
        selectProject(project.id)


@click.group()
@utils.onBeforeCommandExecute(user.initializeUserSession)
def project() -> None:
    pass


project.add_command(create, "create")
project.add_command(edit, "edit")
project.add_command(select, "select")
