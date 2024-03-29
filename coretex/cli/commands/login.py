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

import click

from ..modules.user import authenticate
from ..modules.ui import clickPrompt, stdEcho, successEcho
from ...configuration import UserConfiguration


@click.command()
def login() -> None:
    config = UserConfiguration()
    if config.isUserConfigured():
        if not clickPrompt(
            f"User already logged in with username {config.username}.\nWould you like to log in with a different user (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    stdEcho("Please enter your credentials:")
    loginInfo = authenticate()
    config.saveLoginData(loginInfo)

    successEcho(f"User {config.username} successfully logged in.")
