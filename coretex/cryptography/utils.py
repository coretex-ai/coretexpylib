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

from base64 import b64decode

import os


def _projectKeyEnvName(projectId: int) -> str:
    return f"CTX_PROJECT_KEY_{projectId}"


def getProjectKey(projectId: int) -> bytes:
    """
        Retrieves encryption key for provided project if
        the executing machine has been authorized to access it

        Parameters
        ----------
        projectId : int
            project whose key is being retrieved

        Returns
        -------
        bytes -> encryption key
    """

    envName = _projectKeyEnvName(projectId)
    if envName not in os.environ:
        raise RuntimeError(f"Not authorized to access project: {projectId}")

    encodedKey = os.environ[envName]
    return b64decode(encodedKey)
