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

from typing import List, Any, Optional, Callable
from functools import wraps
from importlib.metadata import version as getLibraryVersion

import sys
import logging

from py3nvml import py3nvml

import click
import requests

from . import ui
from ...utils.process import command


def updateLib() -> None:
    command([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "coretex"], ignoreStdout = True, ignoreStderr = True)


def fetchLatestVersion() -> Optional[str]:
    url = "https://pypi.org/pypi/coretex/json"
    response = requests.get(url)

    if not response.ok:
        logging.getLogger("cli").debug(f"Failed to fetch version of coretex library. Response code: {response.status_code}")
        return None

    data = response.json()
    infoDict = data.get("info")
    if not isinstance(infoDict, dict):
        logging.getLogger("cli").debug("Value of json field of key \"info\" in \"data\" dictionary is not of expected type (dict).")
        return None

    version = infoDict.get("version")
    if not isinstance(version, str):
        logging.getLogger("cli").debug("Value of json field of key \"version\" in \"info\" dictionary is not of expected type (str).")
        return None

    return version


def isVersionStrValid(version: str) -> bool:
    parts = version.split('.')

    if len(parts) != 3:
        return False

    return all(part.isdigit() for part in parts)


def checkLibVersion() -> None:
    current = getLibraryVersion("coretex")
    latest = fetchLatestVersion()

    if not isinstance(latest, str):
        logging.getLogger("cli").debug(f"Invalid type of \"latest\" var {type(current)}. Expected \"string\".")
        return

    if not isVersionStrValid(current):
        logging.getLogger("cli").debug("Current version returned by importlib library is not valid.")
        return

    if not isVersionStrValid(latest):
        logging.getLogger("cli").debug("Latest version extracted from pypi website is not valid.")
        return

    majorCurrent, minorCurrent, patchCurrent = map(int, current.split('.'))
    majorLatest, minorLatest, patchLatest = map(int, latest.split('.'))

    if (majorLatest, minorLatest, patchLatest) > (majorCurrent, minorCurrent, patchCurrent):
        ui.warningEcho(f"Newer version of Coretex library is available. Current: {current}, Latest: {latest}.")
        ui.stdEcho("Use \"coretex update\" command to update library to latest version.")


def isGPUAvailable() -> bool:
    try:
        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
        return False


def onBeforeCommandExecute(fun: Callable[..., Any], excludeOptions: Optional[List[str]] = None) -> Any:
    if excludeOptions is None:
        excludeOptions = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in excludeOptions and value:
                    return f(*args, **kwargs)

            fun()
            return f(*args, **kwargs)
        return wrapper
    return decorator
