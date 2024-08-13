from typing import Optional

import logging

import click

from . import ui
from ...configuration import UserConfiguration
from ...entities import Project, ProjectType, ProjectVisibility
from ...networking import NetworkRequestError


def selectProjectType() -> ProjectType:
    availableProjectTypes = {
        "Computer Vision": ProjectType.computerVision,
        "Motion Recognition": ProjectType.motionRecognition,
        "Bioinformatics": ProjectType.bioInformatics,
        "Other": ProjectType.other
    }

    choices = list(availableProjectTypes.keys())
    selectedChoice = ui.arrowPrompt(choices, "Specify type of project that you wish to create")

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


def promptProjectCreate(message: str, name: str) -> Optional[Project]:
    if not click.confirm(message, default = True):
        return None

    selectedProjectType = selectProjectType()

    try:
        project = Project.createProject(name, selectedProjectType)
        ui.successEcho(f"Project \"{name}\" created successfully.")
        ui.stdEcho(f"A new Project has been created. You can open it by clicking on this URL {ui.outputUrl(project.entityUrl())}.")
        return project
    except NetworkRequestError as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise click.ClickException(f"Failed to create project \"{name}\".")


def promptProjectSelect(userConfig: UserConfiguration) -> Optional[Project]:
    name = ui.clickPrompt("Specify project name that you wish to select")

    ui.progressEcho("Validating project...")
    try:
        project = Project.fetchOne(name = name)
        ui.successEcho(f"Project \"{name}\" selected successfully!")
        userConfig.selectProject(project.id)
    except ValueError:
        ui.errorEcho(f"Project \"{name}\" not found.")
        newProject = promptProjectCreate("Do you want to create a project with that name?", name)
        if newProject is None:
            return None

        userConfig.selectProject(project.id)

    return project


def createProject(name: Optional[str] = None, projectType: Optional[int] = None, description: Optional[str] = None) -> Project:
    if name is None:
        name = ui.clickPrompt("Please enter name of the project you want to create", type = str)

    if projectType is None:
        projectType = selectProjectType()
    else:
        projectType = ProjectType(projectType)

    if description is None:
        description = ui.clickPrompt("Please enter your project's description", type = str, default = "", show_default = False)

    try:
        project = Project.createProject(name, projectType, description = description)
        ui.successEcho(f"Project \"{name}\" created successfully.")
        ui.stdEcho(f"A new Project has been created. You can open it by clicking on this URL {ui.outputUrl(project.entityUrl())}.")
        return project
    except NetworkRequestError as ex:
        logging.getLogger("cli").debug(ex, exc_info = ex)
        raise click.ClickException(f"Failed to create project \"{name}\".")


def getProject(name: Optional[str], userConfig: UserConfiguration) -> Optional[Project]:
    projectId = userConfig.projectId
    if name is not None:
        try:
            return Project.fetchOne(name = name)
        except:
            if projectId is None:
                return promptProjectCreate("Project not found. Do you want to create a new Project with that name?", name)

            return Project.fetchById(projectId)

    if projectId is None:
        ui.stdEcho("To use this command you need to have a Project selected.")
        if click.confirm("Would you like to select an existing Project?", default = True):
            return promptProjectSelect(userConfig)

        if not click.confirm("Would you like to create a new Project?", default = True):
            return None

        return createProject(name)

    return Project.fetchById(projectId)
