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

# Internal - not for outside use
from .configuration import _syncConfigWithEnv
_syncConfigWithEnv()


# Internal - not for outside use
from ._logger import _initializeDefaultLogger, _initializeCLILogger
from .utils import isCliRuntime


if isCliRuntime():
    _initializeCLILogger()
else:
    _initializeDefaultLogger()


# Use this only
from .entities import *
from ._task import currentTaskRun, initializeRTask, TaskRunWorker
from ._folder_manager import folder_manager
