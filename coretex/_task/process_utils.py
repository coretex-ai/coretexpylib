from typing import List, Any
from pathlib import Path

import os
import logging
import subprocess

from threading import Thread

from . import LoggerUploadWorker
from ..entities import Log, LogSeverity


runLogger = logging.getLogger("coretex-run")


def _handleOutput(process: subprocess.Popen, worker: LoggerUploadWorker) -> None:
    stdout = process.stdout
    if stdout is None:
        raise ValueError("stdout is None for subprocess")

    while process.poll() is None:
        line: str = stdout.readline().decode("UTF-8")
        if line.strip() == "":
            continue

        line = line.rstrip()
        worker.add(Log.create(line, LogSeverity.info))
        runLogger.info(line)


def _handleError(process: subprocess.Popen, worker: LoggerUploadWorker, isEnabled: bool) -> None:
    stderr = process.stderr
    if stderr is None:
        raise ValueError("stderr is None for subprocess")

    lines: List[str] = []
    while process.poll() is None:
        line: str = stderr.readline().decode("UTF-8")
        if line.strip() == "":
            continue

        lines.append(line.rstrip())

    # Dump stderr output at the end to perserve stdout order
    for line in lines:
        if isEnabled and process.returncode == 0:
            severity = LogSeverity.warning
        elif isEnabled:
            severity = LogSeverity.fatal
        else:
            # We always want to know what gets logged to stderr
            severity = LogSeverity.debug

        worker.add(Log.create(line, severity))
        runLogger.log(severity.stdSeverity, line)


def executeProcess(
    args: List[str],
    worker: Any,
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
        target = _handleOutput,
        args = (process, worker),
        name = "Process stdout reader"
    ).start()

    if captureErr:
        # Run a thread which captures process stderr and dumps it out node log file
        Thread(
            target = _handleError,
            args = (process, worker, captureErr),
            name = "Process stderr reader"
        ).start()

    return process.wait()
