import click

from ..modules.user_interface import clickPrompt, progressEcho, successEcho
from ..modules.user import authenticate, saveLoginData
from ...configuration import loadConfig, saveConfig, isUserConfigured


@click.command()
def login() -> None:
    config = loadConfig()
    if isUserConfigured(config):
        if not clickPrompt(
            f"User already logged in with username {config['username']}. Would you like to log in with different user (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    progressEcho("Authenticating...")
    loginInfo = authenticate()
    config = saveLoginData(loginInfo, config)

    saveConfig(config)

    successEcho(f"User {config['username']} successfully logged in.")
