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

from ..modules.ui import arrowPrompt, stdEcho, successEcho, progressEcho, errorEcho
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

    selectedChoice = arrowPrompt(choices, "Specify type of project that you wish to create:")

    selectedProjectType = availableProjectTypes[selectedChoice]
    stdEcho(f"You've chosen: {selectedChoice}")
    return selectedProjectType


@click.command()
@click.option("--name", "-n", type = str, help = "Project name")
@click.option("--id", type = int, help = "Project ID")
def select(name: Optional[str], id: Optional[int]) -> None:
    if name is None and id is None:
        raise click.UsageError("Please use either --name / -n (for project name) or --id (for project ID)")

    if name is not None:
        progressEcho("Validating project...")
        try:
            project = Project.fetchOne(name = name)
            successEcho(f"Project \"{name}\" selected successfully!")
            selectProject(project.id)
        except ValueError:
            errorEcho(f"Could not find project with name \"{name}\"")
            if click.confirm("Do you want to create a project with that name?", default = True):
                selectedProjectType = selectProjectType()
                newProject = Project.createProject(name, selectedProjectType)

                successEcho(f"Project with name \"{name}\" successfully created and selected.")
                selectProject(newProject.id)

    if id is not None:
        progressEcho("Validating project...")
        try:
            project = Project.fetchById(id)
            successEcho(f"Project with id \"{id}\" fetched successfully. Project name \"{project.name}\"")
            selectProject(project.id)
        except NetworkRequestError:
            errorEcho(f"Failed to fetch project with provided id \"{id}\"")


@click.group()
def project() -> None:
    pass


project.add_command(select, "select")
