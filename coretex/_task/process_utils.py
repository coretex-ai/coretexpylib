from typing import List, Any
from pathlib import Path

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

        worker.add(Log.create(line.rstrip(), LogSeverity.info))
        runLogger.info(line.rstrip())


def _handleError(process: subprocess.Popen, worker: LoggerUploadWorker, isEnabled: bool) -> None:
    stderr = process.stderr
    if stderr is None:
        raise ValueError("stderr is None for subprocess")

    lines: List[str] = []
    while process.poll() is None:
        line: str = stderr.readline().decode("UTF-8")
        if line.strip() == "":
            continue

        worker.add(Log.create(line.rstrip(), LogSeverity.error))
        lines.append(line.rstrip())

    # Dump stderr output at the end to perserve stdout order
    for line in lines:
        if isEnabled and process.returncode == 0:
            runLogger.warning(line)
        elif isEnabled:
            runLogger.error(line)
        else:
            # We always want to know what gets logged to stderr
            runLogger.debug(line)


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
