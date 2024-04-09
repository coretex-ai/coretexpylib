from typing import Optional

import click

from ..modules import project_utils, user, utils, ui
from ...entities import Model
from ...configuration import loadConfig


@click.command()
@click.argument("path", type = click.Path(exists = True, file_okay = False, dir_okay = True))
@click.option("-n", "--name", type = str, required = True)
@click.option("-p", "--project", type = str, required = False, default = None)
@click.option("-a", "--accuracy", type = click.FloatRange(0, 1), required = False, default = 1)
def create(name: str, path: str, project: Optional[str], accuracy: float) -> None:
    config = loadConfig()

    # If project was provided used that, otherwise get the one from config
    # If project that was provided does not exist prompt user to create a new
    # one with that name
    ctxProject = project_utils.getProject(project, config)
    if ctxProject is None:
        return

    ui.progressEcho("Creating the model...")

    model = Model.createProjectModel(name, ctxProject.id, accuracy)
    model.upload(path)

    ui.successEcho(f"Model \"{model.name}\" created successfully")
    ui.stdEcho(f"A new model has been created. You can open it by clicking on this URL {ui.outputUrl(model.entityUrl())}.")


@click.group()
@utils.onBeforeCommandExecute(user.initializeUserSession)
def model() -> None:
    pass


model.add_command(create)
