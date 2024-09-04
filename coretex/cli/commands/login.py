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

from .base import base_command
from ..modules import user, ui
from ...configuration import UserConfiguration, InvalidConfiguration, ConfigurationNotFound, utils


@base_command()
def login() -> None:
    try:
        userConfig = UserConfiguration.load()
        if not ui.clickPrompt(
            f"User already logged in with username {userConfig.username}.\nWould you like to log in with a different user (Y/n)?",
            type = bool,
            default = True,
            show_default = False
        ):
            return

    except (ConfigurationNotFound, InvalidConfiguration):
        pass

    ui.stdEcho("Please enter your credentials:")
    userConfig = user.configUser()

    initialData = utils.fetchInitialData()
    userConfig.frontendUrl = initialData.get("frontend_url", "app.coretex.ai/")

    userConfig.save()
    ui.successEcho(f"User {userConfig.username} successfully logged in.")
