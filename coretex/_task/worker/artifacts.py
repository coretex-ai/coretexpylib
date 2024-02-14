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


from typing import List, Iterator
from pathlib import Path
from contextlib import contextmanager

import logging

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from ...entities import TaskRun


IGNORED_FILES = ["_coretex.py"]


class FileEventHandler(FileSystemEventHandler):

    def __init__(self) -> None:
        super().__init__()

        self.artifactPaths: List[Path] = []

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        filePath = Path(event.src_path)

        if filePath.parent.joinpath(".coretexignore").exists():
            return

        if filePath.name in IGNORED_FILES:
            return

        logging.getLogger("coretex").debug(f">> [Coretex] File created at path \"{filePath}\", adding to artifacts list")
        self.artifactPaths.append(filePath)


@contextmanager
def track(taskRun: TaskRun) -> Iterator[FileEventHandler]:
    # If local use current working dir, else use task path
    root = Path.cwd() if taskRun.isLocal else taskRun.taskPath

    try:
        observer = Observer()
        observer.setName("ArtifactTracker")

        logging.getLogger("coretexpylib").debug(f">> [Coretex] Tracking files created inside \"{root}\"")

        eventHandler = FileEventHandler()
        observer.schedule(eventHandler, root, recursive = True)  # type: ignore[no-untyped-call]
        observer.start()  # type: ignore[no-untyped-call]
        yield eventHandler
    finally:
        observer.stop()  # type: ignore[no-untyped-call]
        observer.join()

        for index, artifactPath in enumerate(eventHandler.artifactPaths):
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Uploading {index + 1}/{len(eventHandler.artifactPaths)} - \"{artifactPath}\"")

            try:
                artifact = taskRun.createArtifact(artifactPath, str(artifactPath.relative_to(root)))
                if artifact is not None:
                    logging.getLogger("coretexpylib").debug(f"\tSuccessfully uploaded artifact")
                else:
                    logging.getLogger("coretexpylib").debug(f"\tFailed to upload artifact")
            except Exception as e:
                logging.getLogger("coretexpylib").error(f"\tError while creating artifact: {e}")
                logging.getLogger("coretexpylib").debug(f"\tError while creating artifact: {e}", exc_info = e)
