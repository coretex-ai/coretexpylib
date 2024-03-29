from typing import Dict, Any, Optional, Type, TypeVar
from abc import abstractmethod
from pathlib import Path

import os
import json

T = TypeVar("T", int, str, bool)

CONFIG_DIR = Path.home().joinpath(".config", "coretex")


class InvalidConfiguration(Exception):
    pass

class BaseConfiguration:
    def __init__(self, path: Path) -> None:
        self._path = path

        if not path.exists():
            self._raw = self.getDefaultConfig()
            self.save()
        else:
            with path.open("r") as file:
                self._raw = json.load(file)

    @classmethod
    @abstractmethod
    def getDefaultConfig(cls) -> Dict[str, Any]:
        pass

    def _value(self, configKey: str, valueType: Type[T], envKey: Optional[str] = None) -> Optional[T]:
        if envKey is not None and envKey in os.environ:
            return valueType(os.environ[envKey])

        return self._raw.get(configKey)

    def getValue(self, configKey: str, valueType: Type[T], envKey: Optional[str] = None) -> T:
        value = self._value(configKey, valueType, envKey)

        if not isinstance(value, valueType):
            raise InvalidConfiguration(f"Invalid {configKey} type \"{type(value)}\", expected: \"{valueType.__name__}\".")

        return value

    def getOptValue(self, configKey: str, valueType: Type[T], envKey: Optional[str] = None) -> Optional[T]:
        value = self._value(configKey, valueType, envKey)

        if not isinstance(value, valueType):
            return None

        return value

    def save(self) -> None:
        with self._path.open("w") as configFile:
            json.dump(self._raw, configFile, indent = 4)
