import click

from ..modules.user import authenticate, saveLoginData
from ..modules.ui import clickPrompt, stdEcho, successEcho
from ...configuration import loadConfig, saveConfig, isUserConfigured


@click.command()
def login() -> None:
    config = loadConfig()
    if isUserConfigured(config):
        if not clickPrompt(
            f"User already logged in with username {config['username']}.\nWould you like to log in with a different user (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    stdEcho("Please enter your credentials:")
    loginInfo = authenticate()
    config = saveLoginData(loginInfo, config)

    saveConfig(config)

    successEcho(f"User {config['username']} successfully logged in.")
