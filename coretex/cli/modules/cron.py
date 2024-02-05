from typing import List
from pathlib import Path

from ...utils import command


def getExisting() -> List[str]:
    _, output, error = command(["crontab", "-l"], ignoreStdout = True, ignoreStderr = True, check = False)
    if error is not None and "no crontab for" in error:
        return []
    if output is not None:
        return [line.strip() for line in output.split("\n") if line.strip()]

    raise ValueError("\"crontab\" is not installed. To enable automatic updates please install \"crontab\"")


def jobExists(script: str) -> bool:
    existingLines = getExisting()
    return any(line.endswith(script) for line in existingLines)


def scheduleJob(configDir: Path, script: str) -> None:
    if jobExists(script):
        return

    existingLines = getExisting()
    cronEntry = f"*/30 * * * * {configDir / script}\n"
    existingLines.append(cronEntry)

    tempCronFilePath = configDir / "temp.cron"
    with tempCronFilePath.open("w") as tempCronFile:
        tempCronFile.write("\n".join(existingLines))

    command(["crontab", str(tempCronFilePath)])
    tempCronFilePath.unlink()
