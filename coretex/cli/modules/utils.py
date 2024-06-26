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

from typing import List, Any, Tuple, Optional, Callable
from functools import wraps

import sys
import venv

from py3nvml import py3nvml

import click
import platform

from ...configuration import DEFAULT_VENV_PATH
from ...utils.process import command


def fetchCtxSource() -> Optional[str]:
    _, output, _ = command(["pip", "freeze"], ignoreStdout = True)
    packages = output.splitlines()

    for package in packages:
        if "coretex" in package:
            return package.replace(" ", "")

    return None


def checkEnvironment() -> None:
    venvPython = DEFAULT_VENV_PATH / "bin" / "python"
    if DEFAULT_VENV_PATH.exists():
        return

    venv.create(DEFAULT_VENV_PATH, with_pip = True)

    if platform.system() == "Windows":
        venvPython = DEFAULT_VENV_PATH / "Scripts" / "python.exe"

    ctxSource = fetchCtxSource()
    if ctxSource is not None:
        command([str(venvPython), "-m", "pip", "install", ctxSource], ignoreStdout = True)


def updateLib() -> None:
    command([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "coretex"], ignoreStdout = True, ignoreStderr = True)


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
