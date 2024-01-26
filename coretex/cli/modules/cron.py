from typing import List

import os
import subprocess

from ...utils import command


def getExisting() -> List[str]:
    _, output, error = command(["crontab", "-l"], check = False)
    if error is not None and "no crontab for" in error:
        return []
    if output is not None:
        return [line.strip() for line in output.split("\n") if line.strip()]

    raise ValueError("\"crontab\" is not installed. To enable automatic updates please install \"crontab\"")


def jobExists(script: str) -> bool:
    existingLines = getExisting()
    return any(line.endswith(script) for line in existingLines)


def scheduleJob(configDir: str, script: str) -> None:
    if jobExists(script):
        return

    existingLines = getExisting()

    cronEntry = f"*/30 * * * * {os.path.join(configDir, script)}"

    existingLines.append(cronEntry)

    tempCronFilePath = os.path.join(configDir, "temp.cron")
    with open(tempCronFilePath, "w") as tempCronFile:
        tempCronFile.write("\n".join(existingLines))

    subprocess.run(["crontab", tempCronFilePath], check=True)
    os.remove(tempCronFilePath)
