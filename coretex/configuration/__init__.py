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

from .user import UserConfiguration, LoginInfo
from .node import NodeConfiguration
from .base import CONFIG_DIR

def _syncConfigWithEnv() -> None:
    # If configuration doesn't exist default one will be created
    # Initialization of User and Node Configuration classes will do
    # the necessary sync between config properties and corresponding
    # environment variables (e.g. storagePath -> CTX_STORAGE_PATH)

    print('sync')

    UserConfiguration()
    NodeConfiguration()
