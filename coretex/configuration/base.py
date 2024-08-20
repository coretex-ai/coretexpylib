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

from typing import Dict, Any, Optional, Type, TypeVar, List, Tuple
from typing_extensions import Self
from abc import abstractmethod
from pathlib import Path

import os
import json


T = TypeVar("T", int, float, str, bool)

CONFIG_DIR = Path.home().joinpath(".config", "coretex")
DEFAULT_VENV_PATH = CONFIG_DIR / "venv"


class InvalidConfiguration(Exception):

    def __init__(self, message: str, errors: List[str]) -> None:
        super().__init__(message)

        self.errors = errors


class ConfigurationNotFound(Exception):
    pass


class BaseConfiguration:

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._raw = raw

    @classmethod
    @abstractmethod
    def getConfigPath(cls) -> Path:
        pass

    @abstractmethod
    def _isConfigValid(self) -> Tuple[bool, List[str]]:
        pass

    @classmethod
    def load(cls) -> Self:
        configPath = cls.getConfigPath()
        if not configPath.exists():
            raise ConfigurationNotFound(f"Configuration not found at path: {configPath}")

        with configPath.open("r") as file:
            raw = json.load(file)

        config = cls(raw)

        isValid, errors = config._isConfigValid()
        if not isValid:
            raise InvalidConfiguration("Invalid configuration found.", errors)

        return config

    def _value(self, configKey: str, valueType: Type[T], envKey: Optional[str] = None) -> Optional[T]:
        if envKey is not None and envKey in os.environ:
            return valueType(os.environ[envKey])

        return self._raw.get(configKey)

    def getValue(self, configKey: str, valueType: Type[T], envKey: Optional[str] = None, default: Optional[T] = None) -> T:
        value = self._value(configKey, valueType, envKey)

        if value is None:
            value = default

        if not isinstance(value, valueType):
            raise TypeError(f"Invalid {configKey} type \"{type(value)}\", expected: \"{valueType.__name__}\".")

        return value

    def getOptValue(self, configKey: str, valueType: Type[T], envKey: Optional[str] = None) -> Optional[T]:
        value = self._value(configKey, valueType, envKey)

        if not isinstance(value, valueType):
            return None

        return value

    def save(self) -> None:
        configPath = self.getConfigPath()

        if not configPath.parent.exists():
            configPath.parent.mkdir(parents = True, exist_ok = True)

        with configPath.open("w") as configFile:
            json.dump(self._raw, configFile, indent = 4)

    def update(self, config: Self) -> None:
        self._raw = config._raw
