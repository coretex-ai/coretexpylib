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

from typing import Any, Optional, Dict
from pathlib import Path

import json


CONFIG_PATH = Path("~/.config/coretex/config.json").expanduser()


# Only used by NetworkManager, should not be used anywhere else
class UserData:

    def __init__(self) -> None:
        with open(CONFIG_PATH, "r") as configFile:
            self.__values: Dict[str, Any] = json.load(configFile)

    def __getOptionalStr(self, key: str) -> Optional[str]:
        value = self.__values[key]
        if value is None:
            return None

        if isinstance(value, str):
            return value

        raise ValueError(f">> [Coretex] {key} is not of type optional str")

    def __setValue(self, key: str, value: Any) -> None:
        if not key in self.__values:
            raise KeyError(f">> [Coretex] {key} not found")

        self.__values[key] = value

        with open(CONFIG_PATH, "w") as configFile:
            json.dump(self.__values, configFile, indent = 4)

    @property
    def hasStoredCredentials(self) -> bool:
        return self.username is not None and self.password is not None

    @property
    def username(self) -> Optional[str]:
        return self.__getOptionalStr("username")

    @username.setter
    def username(self, value: Optional[str]) -> None:
        self.__setValue("username", value)

    @property
    def password(self) -> Optional[str]:
        return self.__getOptionalStr("password")

    @password.setter
    def password(self, value: Optional[str]) -> None:
        self.__setValue("password", value)

    @property
    def apiToken(self) -> Optional[str]:
        return self.__getOptionalStr("token")

    @apiToken.setter
    def apiToken(self, value: Optional[str]) -> None:
        self.__setValue("token", value)

    @property
    def refreshToken(self) -> Optional[str]:
        return self.__getOptionalStr("refreshToken")

    @refreshToken.setter
    def refreshToken(self, value: Optional[str]) -> None:
        self.__setValue("refreshToken", value)
