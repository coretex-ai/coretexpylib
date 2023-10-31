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

from ...entities import TaskRun


class FileEventHandler(FileSystemEventHandler):

    def __init__(self, taskRun: TaskRun, root: Path) -> None:
        super().__init__()

        self.taskRun = taskRun
        self.root = root

    def on_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]) -> None:
        if event.is_directory:
            return

        filePath = Path(event.src_path)
        relativePath = filePath.relative_to(self.root)

        artifact = self.taskRun.createArtifact(filePath, str(relativePath))
        if artifact is None:
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Failed to create artifact from \"{filePath}\"")


def startTracking(taskRun: TaskRun) -> None:
    observer = Observer()
    observer.setName("ArtifactTracker")

    observer.schedule(
        FileEventHandler(taskRun, Path.cwd()),
        Path.cwd(),
        recursive = True
    )  # type: ignore[no-untyped-call]

    observer.start()  # type: ignore[no-untyped-call]
