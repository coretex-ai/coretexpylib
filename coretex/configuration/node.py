from typing import Dict, Any, Optional

import os
import json

from ..configuration import CONFIG_DIR


NODE_CONFIG_PATH = CONFIG_DIR / "node_config.json"


class InvalidNodeConfiguration(Exception):
    pass


def initializeConfig() -> Dict[str, Any]:
    config = {
        "nodeName": os.environ.get("CTX_NODE_NAME"),
        "nodeAccessToken": None,
        "image": "coretexai/coretex-node:latest-cpu",
        "allowGpu": False,
        "nodeRam": None,
        "nodeSharedMemory": None,
        "cpuCount": None,
        "nodeMode": None,
        "allowDocker": False,
        "secretsKey": None,
        "initScript": None
    }

    if not NODE_CONFIG_PATH.exists():
            with NODE_CONFIG_PATH.open("w") as configFile:
                json.dump(config, configFile, indent = 4)
    else:
        with open(NODE_CONFIG_PATH, "r") as file:
            config = json.load(file)

    if not isinstance(config, dict):
        raise InvalidNodeConfiguration(f"Invalid config type \"{type(config)}\", expected: \"dict\".")

    return config


class NodeConfiguration:

    def __init__(self) -> None:
        self._raw = initializeConfig()

    @property
    def nodeName(self) -> str:
        return self.getStrValue("nodeName", "CTX_NODE_NAME")

    @nodeName.setter
    def nodeName(self, value: Optional[str]) -> None:
        self._raw["nodeName"] = value

    @property
    def nodeAccessToken(self) -> str:
        return self.getStrValue("nodeAccessToken")

    @nodeAccessToken.setter
    def nodeAccessToken(self, value: Optional[str]) -> None:
        self._raw["nodeAccessToken"] = value

    @property
    def image(self) -> str:
        return self.getStrValue("image", "CTX_NODE_NAME")

    @image.setter
    def image(self, value: Optional[str]) -> None:
        self._raw["image"] = value

    @property
    def allowGpu(self) -> str:
        return self.getStrValue("allowGpu")

    @allowGpu.setter
    def allowGpu(self, value: Optional[bool]) -> None:
        self._raw["allowGpu"] = value

    @property
    def nodeRam(self) -> int:
        return self.getIntValue("nodeRam")

    @nodeRam.setter
    def nodeRam(self, value: Optional[int]) -> None:
        self._raw["nodeRam"] = value

    @property
    def nodeSwap(self) -> int:
        return self.getIntValue("nodeSwap")

    @nodeSwap.setter
    def nodeSwap(self, value: Optional[int]) -> None:
        self._raw["nodeSwap"] = value

    @property
    def nodeSharedMemory(self) -> int:
        return self.getIntValue("nodeSharedMemory")

    @nodeSharedMemory.setter
    def nodeSharedMemory(self, value: Optional[int]) -> None:
        self._raw["nodeSharedMemory"] = value

    @property
    def cpuCount(self) -> int:
        return self.getIntValue("cpuCount")

    @cpuCount.setter
    def cpuCount(self, value: Optional[int]) -> None:
        self._raw["cpuCount"] = value

    @property
    def nodeMode(self) -> int:
        return self.getIntValue("nodeMode")

    @nodeMode.setter
    def nodeMode(self, value: Optional[int]) -> None:
        self._raw["nodeMode"] = value

    @property
    def allowDocker(self) -> bool:
        return self.getBoolValue("allowDocker")

    @allowDocker.setter
    def allowDocker(self, value: Optional[bool]) -> None:
        self._raw["allowDocker"] = value

    @property
    def secretsKey(self) -> str:
        return self.getStrValue("secretsKey")

    @secretsKey.setter
    def secretsKey(self, value: Optional[str]) -> None:
        self._raw["secretsKey"] = value

    @property
    def initScript(self) -> str:
        return self.getStrValue("initScript")

    @initScript.setter
    def initScript(self, value: Optional[str]) -> None:
        self._raw["initScript"] = value

    def getStrValue(self, configKey: str, envKey: Optional[str] = None) -> str:
        if envKey is not None and envKey in os.environ:
            return os.environ[envKey]

        value = self._raw.get(configKey)

        if not isinstance(value, str):
            raise InvalidNodeConfiguration(f"Invalid f{configKey} type \"{type(value)}\", expected: \"str\".")

        return value

    def getIntValue(self, configKey: str, envKey: Optional[str] = None) -> int:
        if envKey is not None and envKey in os.environ:
            return int(os.environ[envKey])

        value = self._raw.get(configKey)

        if not isinstance(value, int):
            raise InvalidNodeConfiguration(f"Invalid f{configKey} type \"{type(value)}\", expected: \"int\".")

        return value

    def getBoolValue(self, configKey: str, envKey: Optional[str] = None) -> bool:
        if envKey is not None and envKey in os.environ:
            return bool(os.environ[envKey])

        value = self._raw.get(configKey)

        if not isinstance(value, bool):
            raise InvalidNodeConfiguration(f"Invalid f{configKey} type \"{type(value)}\", expected: \"bool\".")

        return value
