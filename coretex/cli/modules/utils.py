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

from ...configuration import DEFAULT_VENV_PATH
from ...utils.process import command


def checkEnvironment() -> None:
    if DEFAULT_VENV_PATH.exists():
        return
    venv.create(DEFAULT_VENV_PATH, with_pip = True)
    venvPython = DEFAULT_VENV_PATH / "bin" / "python"
    command([str(venvPython), "-m", "pip", "install", "coretex"])


def updateLib() -> None:
    command([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "coretex"], ignoreStdout = True, ignoreStderr = True)


def getExecPaths() -> Tuple[str, str]:
    _, dockerPath, _ = command(["which", "docker"], ignoreStdout = True, ignoreStderr = True)
    _, gitPath, _ = command(["which", "git"], ignoreStdout = True, ignoreStderr = True)

    dockerPathParts = dockerPath.strip().split('/')
    dockerExecPath = '/'.join(dockerPathParts[:-1])

    gitPathParts = gitPath.strip().split('/')
    gitExecPath = '/'.join(gitPathParts[:-1])

    return dockerExecPath, gitExecPath


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
