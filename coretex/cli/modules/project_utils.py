from typing import Optional, Dict, Any
from enum import IntEnum

import click

from . import ui
from ...entities import Project, ProjectType, ProjectVisibility
from ...networking import EntityNotCreated, NetworkResponse, networkManager
from ...configuration import loadConfig, saveConfig


class EntityVisibilityType(IntEnum):

    project = 1
    node    = 2


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
    selectedChoice = ui.arrowPrompt(choices, "Specify type of project that you wish to create:")

    selectedProjectType = availableProjectTypes[selectedChoice]
    ui.stdEcho(f"You've chosen: {selectedChoice}")
    return selectedProjectType


def selectProjectVisibility() -> ProjectVisibility:
    availableProjectVisibilities = {
        "Private": ProjectVisibility.private,
        "Public": ProjectVisibility.public,
    }

    choices = list(availableProjectVisibilities.keys())
    selectedChoice = ui.arrowPrompt(choices, "Specify visibility of project:")

    selectedProjectVisibility = availableProjectVisibilities[selectedChoice]
    ui.stdEcho(f"You've chosen: {selectedChoice}")
    return selectedProjectVisibility


def changeProjectVisibility(id: int, visibility: ProjectVisibility) -> NetworkResponse:
    return networkManager.post("entity-visibility", {
        "entity_id": id,
        "type": EntityVisibilityType.project,
        "visibility": visibility,
    })


def promptProjectCreate(message: str, name: str) -> Optional[Project]:
    if not click.confirm(message, default = True):
        return None

    selectedProjectType = selectProjectType()

    try:
        project = Project.createProject(name, selectedProjectType)
        ui.successEcho(f"Project \"{name}\" created successfully.")

        return project
    except EntityNotCreated:
        raise click.ClickException(f"Failed to create project \"{name}\".")


def getProject(name: Optional[str], config: Dict[str, Any]) -> Optional[Project]:
    if name is not None:
        try:
            return Project.fetchOne(name = name)
        except:
            return promptProjectCreate("Project not found. Do you want to create a new Project with that name?", name)

    projectId = config.get("projectId")
    if projectId is not None:
        return Project.fetchById(projectId)

    # Generic message on how to specify the Project
    raise click.ClickException(
        "Project was not provided.\n"
        "Project can be selected globally by using \"coretex project select\" command\n"
        "or you can pass the Project directly to this command using \"--project\" option"
    )
