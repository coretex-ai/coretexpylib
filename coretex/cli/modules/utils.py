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

from typing import Tuple, Optional
from pathlib import Path
from importlib.metadata import version as getLibraryVersion

import sys
import venv
import shutil
import logging
import platform

from py3nvml import py3nvml

import requests

from . import ui
from ...configuration import DEFAULT_VENV_PATH
from ...utils.process import command


def formatCliVersion(version: Tuple[int, int, int]) -> str:
    return ".".join(map(str, version))


def fetchCtxSource() -> Optional[str]:
    _, output, _ = command([sys.executable, "-m", "pip", "freeze"], ignoreStdout = True, ignoreStderr = True)
    packages = output.splitlines()

    for package in packages:
        if "coretex" in package:
            return package.replace(" ", "")

    return None


def createEnvironment(venvPython: Path) -> None:
    if DEFAULT_VENV_PATH.exists():
        shutil.rmtree(DEFAULT_VENV_PATH)

    venv.create(DEFAULT_VENV_PATH, with_pip = True)

    if platform.system() == "Windows":
        venvPython = DEFAULT_VENV_PATH / "Scripts" / "python.exe"

    ctxSource = fetchCtxSource()
    if ctxSource is not None:
        command([str(venvPython), "-m", "pip", "install", ctxSource], ignoreStdout = True, ignoreStderr = True)


def checkEnvironment() -> None:
    venvPython = DEFAULT_VENV_PATH / "bin" / "python"
    venvActivate = DEFAULT_VENV_PATH / "bin" / "activate"
    venvCoretex =  DEFAULT_VENV_PATH / "bin" / "coretex"

    if not venvActivate.exists() or not venvPython.exists():
        createEnvironment(venvPython)
        return

    try:
        command([str(venvCoretex), "version"], check = True, ignoreStderr = True, ignoreStdout = True)
    except Exception:
        createEnvironment(venvPython)
        return


def updateLib() -> None:
    command([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "coretex"], ignoreStdout = True, ignoreStderr = True)


def parseLibraryVersion(version: str) -> Optional[Tuple[int, int, int]]:
    parts = version.split(".")

    if len(parts) != 3:
        return None

    if all(part.isdigit() for part in parts):
        major, minor, patch = map(int, version.split('.'))
        return major, minor, patch

    return None


def fetchCurrentVersion() -> Optional[Tuple[int, int, int]]:
    version = parseLibraryVersion(getLibraryVersion("coretex"))
    if version is None:
        logging.getLogger("cli").debug(f"Couldn't parse current version from string: {version}")
        return None

    return version


def fetchLatestVersion() -> Optional[Tuple[int, int, int]]:
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

    parsedVersion = parseLibraryVersion(version)
    if parsedVersion is None:
        logging.getLogger("cli").debug(f"Couldn't parse latest version from string: {version}")
        return None

    return parsedVersion


def checkLibVersion() -> None:
    currentVersion = fetchCurrentVersion()
    latestVersion = fetchLatestVersion()

    if currentVersion is None or latestVersion is None:
        return

    if latestVersion > currentVersion:
        ui.warningEcho(
            f"Newer version of Coretex library is available. "
            f"Current: {formatCliVersion(currentVersion)}, Latest: {formatCliVersion(latestVersion)}."
        )
        ui.stdEcho("Use \"coretex update\" command to update library to latest version.")


def getExecPath(executable: str) -> str:
    _, path, _ = command(["which", executable], ignoreStdout = True, ignoreStderr = True)
    pathParts = path.strip().split('/')
    execPath = '/'.join(pathParts[:-1])

    return execPath


def isGPUAvailable() -> bool:
    try:
        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
        return False
