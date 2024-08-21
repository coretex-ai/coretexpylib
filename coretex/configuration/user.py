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

from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from .base import BaseConfiguration, CONFIG_DIR
from ..utils import decodeDate


class UserConfiguration(BaseConfiguration):

    @classmethod
    def getConfigPath(cls) -> Path:
        return CONFIG_DIR / "user_config.json"

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
        return self.getValue("serverUrl", str, "CTX_API_URL", "https://api.coretex.ai/")

    @serverUrl.setter
    def serverUrl(self, value: str) -> None:
        self._raw["serverUrl"] = value

    @property
    def projectId(self) -> Optional[int]:
        return self.getOptValue("projectId", int, "CTX_PROJECT_ID")

    @projectId.setter
    def projectId(self, value: Optional[int]) -> None:
        self._raw["projectId"] = value

    def _isConfigValid(self) -> Tuple[bool, List[str]]:
        isValid = True
        errorMessages = []

        if self._raw.get("username") is None or not isinstance(self._raw.get("username"), str):
            isValid = False
            errorMessages.append("Missing required field \"username\" in user configuration.")

        if self._raw.get("password") is None or not isinstance(self._raw.get("password"), str):
            isValid = False
            errorMessages.append("Missing required field \"password\" in user configuration.")

        return isValid, errorMessages

    def isTokenValid(self, tokenName: str) -> bool:
        tokenValue = self._raw.get(tokenName)
        if not isinstance(tokenValue, str) or len(tokenValue) == 0:
            return False

        tokenExpirationDate = self._raw.get(f"{tokenName}ExpirationDate")
        if not isinstance(tokenExpirationDate, str) or len(tokenExpirationDate) == 0:
            return False

        try:
            return datetime.now(timezone.utc) < decodeDate(tokenExpirationDate)
        except ValueError:
            return False

    def selectProject(self, id: int) -> None:
        self.projectId = id
        self.save()
