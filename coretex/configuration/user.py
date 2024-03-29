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

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

import os

from .base import BaseConfiguration, CONFIG_DIR
from ..utils import decodeDate


USER_CONFIG_PATH = CONFIG_DIR / "user_config.json"
USER_DEFAULT_CONFIG = {
    "username": os.environ.get("CTX_USERNAME"),
    "password": os.environ.get("CTX_PASSWORD"),
    "token": None,
    "refreshToken": None,
    "tokenExpirationDate": None,
    "refreshTokenExpirationDate": None,
    "serverUrl": os.environ.get("CTX_API_URL", "https://api.coretex.ai/"),
    "projectId": os.environ.get("CTX_PROJECT_ID")
}


class InvalidUserConfiguration(Exception):
    pass


@dataclass
class LoginInfo:

    username: str
    password: str
    token: str
    tokenExpirationDate: str
    refreshToken: str
    refreshTokenExpirationDate: str


def hasExpired(tokenExpirationDate: Optional[str]) -> bool:
    if tokenExpirationDate is None:
        return False

    currentDate = datetime.utcnow().replace(tzinfo = timezone.utc)
    return currentDate >= decodeDate(tokenExpirationDate)


class UserConfiguration(BaseConfiguration):

    def __init__(self) -> None:
        super().__init__(USER_CONFIG_PATH)
        if not "CTX_API_URL" in os.environ:
            os.environ["CTX_API_URL"] = self.serverUrl

    @classmethod
    def getDefaultConfig(cls) -> Dict[str, Any]:
        return USER_DEFAULT_CONFIG

    @property
    def username(self) -> str:
        return self.getValue("username", str, "CTX_USERNAME")

    @username.setter
    def username(self, value: str) -> None:
        self._raw["username"] = value

    @property
    def password(self) -> str:
        return self.getValue("password", str, "CTX_PASSWORD")

    @password.setter
    def password(self, value: str) -> None:
        self._raw["password"] = value

    @property
    def token(self) -> Optional[str]:
        return self.getOptValue("token", str)

    @token.setter
    def token(self, value: Optional[str]) -> None:
        self._raw["token"] = value

    @property
    def refreshToken(self) -> Optional[str]:
        return self.getOptValue("refreshToken", str)

    @refreshToken.setter
    def refreshToken(self, value: Optional[str]) -> None:
        self._raw["refreshToken"] = value

    @property
    def tokenExpirationDate(self) -> Optional[str]:
        return self.getOptValue("tokenExpirationDate", str)

    @tokenExpirationDate.setter
    def tokenExpirationDate(self, value: Optional[str]) -> None:
        self._raw["tokenExpirationDate"] = value

    @property
    def refreshTokenExpirationDate(self) -> Optional[str]:
        return self.getOptValue("refreshTokenExpirationDate", str)

    @refreshTokenExpirationDate.setter
    def refreshTokenExpirationDate(self, value: Optional[str]) -> None:
        self._raw["refreshTokenExpirationDate"] = value

    @property
    def serverUrl(self) -> str:
        return self.getValue("serverUrl", str, "CTX_API_URL")

    @serverUrl.setter
    def serverUrl(self, value: str) -> None:
        self._raw["serverUrl"] = value

    @property
    def projectId(self) -> Optional[int]:
        return self.getOptValue("projectId", int, "CTX_PROJECT_ID")

    @projectId.setter
    def projectId(self, value: Optional[int]) -> None:
        self._raw["projectId"] = value

    @property
    def isValid(self) -> bool:
        return self._raw.get("username") is not None and self._raw.get("password") is not None

    @property
    def hasTokenExpired(self) -> bool:
        if self.token is None:
            return True

        if self.tokenExpirationDate is None:
            return True

        return hasExpired(self.tokenExpirationDate)

    @property
    def hasRefreshTokenExpired(self) -> bool:
        if self.refreshToken is None:
            return True

        if self.refreshTokenExpirationDate is None:
            return True

        return hasExpired(self.refreshTokenExpirationDate)

    def isUserConfigured(self) -> bool:
        if self._raw.get("username") is None or not isinstance(self._raw.get("username"), str):
            return False

        if self._raw.get("password") is None or not isinstance(self._raw.get("password"), str):
            return False

        return True

    def saveLoginData(self, loginInfo: LoginInfo) -> None:
        self.username = loginInfo.username
        self.password = loginInfo.password
        self.token = loginInfo.token
        self.tokenExpirationDate = loginInfo.tokenExpirationDate
        self.refreshToken = loginInfo.refreshToken
        self.refreshTokenExpirationDate = loginInfo.refreshTokenExpirationDate

        self.save()
