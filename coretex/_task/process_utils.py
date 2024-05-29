from typing import List
from pathlib import Path

import subprocess

from threading import Thread

from .run_logger import runLogger
from ..logging import LogSeverity


def captureRunStdout(process: subprocess.Popen) -> None:
    stdout = process.stdout
    if stdout is None:
        raise ValueError("stdout is None for subprocess")

    while process.poll() is None:
        line: str = stdout.readline().decode("UTF-8")
        runLogger.logProcessOutput(line)


def captureRunStderr(process: subprocess.Popen, isEnabled: bool) -> None:
    stderr = process.stderr
    if stderr is None:
        raise ValueError("stderr is None for subprocess")

    lines: List[str] = []
    while process.poll() is None:
        line: str = stderr.readline().decode("UTF-8")
        lines.append(line)

    # Dump stderr output at the end to perserve stdout order
    for line in lines:
        if isEnabled and process.returncode == 0:
            severity = LogSeverity.warning
        elif isEnabled:
            severity = LogSeverity.fatal
        else:
            # We always want to know what gets logged to stderr
            severity = LogSeverity.debug

        runLogger.logProcessOutput(line, severity)


def executeRunLocally(
    args: List[str],
    captureErr: bool,
    cwd: Path = Path.cwd()
) -> int:

    process = subprocess.Popen(
        args,
        shell = False,
        cwd = cwd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    # Run a thread which captures process stdout and prints it out to Coretex.ai console
    Thread(
        target = captureRunStdout,
        args = (process,),
        name = "Process stdout reader"
    ).start()

    if captureErr:
        # Run a thread which captures process stderr and dumps it out node log file
        Thread(
            target = captureRunStderr,
            args = (process, captureErr),
            name = "Process stderr reader"
        ).start()

    return process.wait()
