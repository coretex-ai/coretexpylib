from typing import Dict, Any, Optional, TypeVar
from pathlib import Path

import os
import sys

from .base import BaseConfiguration, CONFIG_DIR




def getEnvVar(key: str, default: str) -> str:
    if os.environ.get(key) is None:
        return default

    return os.environ[key]


NODE_CONFIG_PATH = CONFIG_DIR / "node_config.json"
NODE_DEFAULT_CONFIG = {
    "nodeName": os.environ.get("CTX_NODE_NAME"),
    "nodeAccessToken": None,
    "storagePath": getEnvVar("CTX_STORAGE_PATH", "~/.coretex"),
    "image": "coretexai/coretex-node:latest-cpu",
    "allowGpu": False,
    "nodeRam": None,
    "nodeSharedMemory": None,
    "cpuCount": None,
    "nodeMode": None,
    "allowDocker": False,
    "secretsKey": None,
    "initScript": None,
    "modelId": None,
}


def isCliRuntime() -> bool:
    executablePath = sys.argv[0]
    return (
        executablePath.endswith("/bin/coretex") and
        os.access(executablePath, os.X_OK)
    )


class InvalidNodeConfiguration(Exception):
    pass


class NodeConfiguration(BaseConfiguration):

    def __init__(self) -> None:
        super().__init__(NODE_CONFIG_PATH)
        secretsKey = self.secretsKey
        if isinstance(secretsKey, str) and secretsKey != "":
            os.environ["CTX_SECRETS_KEY"] = secretsKey

        if not isCliRuntime():
            os.environ["CTX_STORAGE_PATH"] = self.storagePath
        else:
            os.environ["CTX_STORAGE_PATH"] = f"{CONFIG_DIR}/data"

    @classmethod
    def getDefaultConfig(cls) -> Dict[str, Any]:
        return NODE_DEFAULT_CONFIG

    @property
    def nodeName(self) -> str:
        return self.getValue("nodeName", str, "CTX_NODE_NAME")

    @nodeName.setter
    def nodeName(self, value: str) -> None:
        self._raw["nodeName"] = value

    @property
    def nodeAccessToken(self) -> str:
        return self.getValue("nodeAccessToken", str)

    @nodeAccessToken.setter
    def nodeAccessToken(self, value: str) -> None:
        self._raw["nodeAccessToken"] = value

    @property
    def storagePath(self) -> str:
        return self.getValue("storagePath", str, "CTX_STORAGE_PATH")

    @storagePath.setter
    def storagePath(self, value: Optional[str]) -> None:
        self._raw["storagePath"] = value

    @property
    def image(self) -> str:
        return self.getValue("image", str)

    @image.setter
    def image(self, value: str) -> None:
        self._raw["image"] = value

    @property
    def allowGpu(self) -> bool:
        return self.getValue("allowGpu", bool)

    @allowGpu.setter
    def allowGpu(self, value: bool) -> None:
        self._raw["allowGpu"] = value

    @property
    def nodeRam(self) -> int:
        return self.getValue("nodeRam", int)

    @nodeRam.setter
    def nodeRam(self, value: int) -> None:
        self._raw["nodeRam"] = value

    @property
    def nodeSwap(self) -> int:
        return self.getValue("nodeSwap", int)

    @nodeSwap.setter
    def nodeSwap(self, value: int) -> None:
        self._raw["nodeSwap"] = value

    @property
    def nodeSharedMemory(self) -> int:
        return self.getValue("nodeSharedMemory", int)

    @nodeSharedMemory.setter
    def nodeSharedMemory(self, value: int) -> None:
        self._raw["nodeSharedMemory"] = value

    @property
    def cpuCount(self) -> int:
        return self.getValue("cpuCount", int)

    @cpuCount.setter
    def cpuCount(self, value: int) -> None:
        self._raw["cpuCount"] = value

    @property
    def nodeMode(self) -> int:
        return self.getValue("nodeMode", int)

    @nodeMode.setter
    def nodeMode(self, value: int) -> None:
        self._raw["nodeMode"] = value

    @property
    def allowDocker(self) -> bool:
        return self.getValue("allowDocker", bool)

    @allowDocker.setter
    def allowDocker(self, value: bool) -> None:
        self._raw["allowDocker"] = value

    @property
    def secretsKey(self) -> Optional[str]:
        return self.getOptValue("secretsKey", str)

    @secretsKey.setter
    def secretsKey(self, value: Optional[str]) -> None:
        self._raw["secretsKey"] = value

    @property
    def initScript(self) -> Optional[str]:
        return self.getOptValue("initScript", str)

    @initScript.setter
    def initScript(self, value: Optional[str]) -> None:
        self._raw["initScript"] = value

    @property
    def modelId(self) -> Optional[int]:
        return self.getOptValue("modelId", int)

    @modelId.setter
    def modelId(self, value: Optional[int]) -> None:
        self._raw["modelId"] = value

    def isNodeConfigured(self) -> bool:
        return False

    def getInitScriptPath(self) -> Optional[Path]:
        value = self._raw.get("initScript")

        if not isinstance(value, str):
            return None

        if value == "":
            return None

        path = Path(value).expanduser().absolute()
        if not path.exists():
            return None

        return path
