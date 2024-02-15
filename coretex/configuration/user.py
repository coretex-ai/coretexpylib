from typing import Dict, Any, Optional, TypeVar
from pathlib import Path
from datetime import datetime, timezone

import os
import json

from ..utils import decodeDate
from ..configuration import CONFIG_DIR


PropertyType = TypeVar("PropertyType")


USER_CONFIG_PATH = CONFIG_DIR / "user_config.json"


class InvalidUserConfiguration(Exception):
    pass


def initializeConfig() -> Dict[str, Any]:
    config = {
        "username": os.environ.get("CTX_USERNAME"),
        "password": os.environ.get("CTX_PASSWORD"),
        "token": None,
        "refreshToken": None,
        "tokenExpirationDate": None,
        "refreshTokenExpirationDate": None,
        "serverUrl": os.environ.get("CTX_API_URL", "https://api.coretex.ai/"),
        "projectId": os.environ.get("CTX_PROJECT_ID")
    }

    if not USER_CONFIG_PATH.exists():
            with USER_CONFIG_PATH.open("w") as configFile:
                json.dump(config, configFile, indent = 4)
    else:
        with open(USER_CONFIG_PATH, "r") as file:
            config = json.load(file)

    if not isinstance(config, dict):
        raise InvalidUserConfiguration(f"Invalid config type \"{type(config)}\", expected: \"dict\".")

    return config


def hasExpired(tokenExpirationDate: Optional[str]) -> bool:
    if tokenExpirationDate is None:
        return False

    currentDate = datetime.utcnow().replace(tzinfo = timezone.utc)
    return currentDate >= decodeDate(tokenExpirationDate)


class UserConfiguration:

    def __init__(self) -> None:
        self._raw = initializeConfig()

    @property
    def username(self) -> str:
        return self.getStrValue("username", "CTX_USERNAME")

    @username.setter
    def username(self, value: Optional[str]) -> None:
        self._raw["username"] = value

    @property
    def password(self) -> str:
        return self.getStrValue("password", "CTX_PASSWORD")

    @password.setter
    def password(self, value: Optional[str]) -> None:
        self._raw["password"] = value

    @property
    def token(self) -> str:
        return self.getStrValue("token")

    @token.setter
    def token(self, value: Optional[str]) -> None:
        self._raw["token"] = value

    @property
    def refreshToken(self) -> str:
        return self.getStrValue("refreshToken")

    @refreshToken.setter
    def refreshToken(self, value: Optional[str]) -> None:
        self._raw["refreshToken"] = value

    @property
    def tokenExpirationDate(self) -> str:
        return self.getStrValue("tokenExpirationDate")

    @tokenExpirationDate.setter
    def tokenExpirationDate(self, value: Optional[str]) -> None:
        self._raw["tokenExpirationDate"] = value

    @property
    def refreshTokenExpirationDate(self) -> str:
        return self.getStrValue("refreshTokenExpirationDate")

    @refreshTokenExpirationDate.setter
    def refreshTokenExpirationDate(self, value: Optional[str]) -> None:
        self._raw["refreshTokenExpirationDate"] = value

    @property
    def serverUrl(self) -> str:
        return self.getStrValue("serverUrl", "CTX_API_URL")

    @serverUrl.setter
    def serverUrl(self, value: Optional[str]) -> None:
        self._raw["serverUrl"] = value

    @property
    def projectId(self) -> int:
        return self.getIntValue("projectId", "CTX_PROJECT_ID")

    @projectId.setter
    def projectId(self, value: Optional[int]) -> None:
        self._raw["projectId"] = value

    @property
    def isValid(self) -> bool:
        return self._raw.get("username") is not None and self._raw.get("password") is not None

    @property
    def hasTokenExpired(self) -> bool:
        if self._raw.get("token") is None:
            return True

        tokenExpirationDate = self._raw.get("tokenExpirationDate")
        if tokenExpirationDate is None:
            return True

        return hasExpired(tokenExpirationDate)

    @property
    def hasRefreshTokenExpired(self) -> bool:
        if self._raw.get("refreshToken") is None:
            return True

        refreshTokenExpirationDate = self._raw.get("refreshTokenExpirationDate")
        if refreshTokenExpirationDate is None:
            return True

        return hasExpired(refreshTokenExpirationDate)

    def save(self) -> None:
        with USER_CONFIG_PATH.open("w") as configFile:
            json.dump(self.__dict__, configFile, indent = 4)

    def getStrValue(self, configKey: str, envKey: Optional[str] = None) -> str:
        if envKey is not None and envKey in os.environ:
            return os.environ[envKey]

        value = self._raw.get(configKey)

        if not isinstance(value, str):
            raise InvalidUserConfiguration(f"Invalid username type \"{type(value)}\", expected: \"str\".")

        return value

    def getIntValue(self, configKey: str, envKey: Optional[str] = None) -> int:
        if envKey is not None and envKey in os.environ:
            return int(os.environ[envKey])

        value = self._raw.get(configKey)

        if not isinstance(value, int):
            raise InvalidUserConfiguration(f"Invalid username type \"{type(value)}\", expected: \"str\".")

        return value
