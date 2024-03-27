from typing import Optional, Dict, Any

import click

from . import ui
from ...entities import Project, ProjectType
from ...networking import EntityNotCreated


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


def promptProjectCreate(message: str, name: str) -> Optional[Project]:
    if not click.confirm(message, default = True):
        raise RuntimeError

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
