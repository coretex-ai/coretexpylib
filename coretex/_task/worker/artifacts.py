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


from typing import Union
from pathlib import Path

import logging

from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileCreatedEvent
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from ...entities import TaskRun


IGNORED_FILES = ["_coretex.py"]


class FileEventHandler(FileSystemEventHandler):

    def __init__(self, taskRun: TaskRun, root: Path) -> None:
        super().__init__()

        self.taskRun = taskRun
        self.root = root

    def on_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]) -> None:
        if event.is_directory:
            return

        filePath = Path(event.src_path)

        if filePath.parent.joinpath(".coretexignore").exists():
            return

        if filePath.name in IGNORED_FILES:
            return

        logging.getLogger("coretex").debug(f">> [Coretex] File created at path \"{filePath}\"")

        relativePath = filePath.relative_to(self.root)
        artifact = self.taskRun.createArtifact(filePath, str(relativePath))

        if artifact is None:
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Failed to create artifact from \"{filePath}\"")


def startTracking(taskRun: TaskRun) -> BaseObserver:
    observer = Observer()
    observer.setName("ArtifactTracker")

    # If local use current working dir, else use task path
    path = Path.cwd() if taskRun.isLocal else taskRun.taskPath
    logging.getLogger("coretexpylib").debug(f">> [Coretex] Tracking files created inside \"{path}\"")

    observer.schedule(
        FileEventHandler(taskRun, path),
        path,
        recursive = True
    )  # type: ignore[no-untyped-call]

    observer.start()  # type: ignore[no-untyped-call]
    return observer
