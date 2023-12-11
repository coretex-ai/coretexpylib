from pathlib import Path

import json


CONFIG_JSON = Path.home() / ".config/coretex/config.json"
SERVER_URL = "https://devext.biomechservices.com:29007/"


def readConfig() -> dict:
    if not CONFIG_JSON.exists():
        CONFIG_JSON.parent.mkdir(exist_ok = True, parents = True)
        with CONFIG_JSON.open("w") as configFile:
            json.dump({"serverUrl": SERVER_URL}, configFile)

    with CONFIG_JSON.open("r") as configFile:
        return json.load(configFile)


def saveConfig(content: dict) -> None:
    with CONFIG_JSON.open("w") as configFile:
        json.dump(content, configFile)
