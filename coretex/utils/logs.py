from pathlib import Path
from logging import FileHandler
from logging.handlers import WatchedFileHandler

import platform


class CoretexFileHandler(WatchedFileHandler):

    def reopenIfNeeded(self) -> None:
        # baseFilename is absoulte path to the log file
        path = Path(self.baseFilename)

        # If parent dir got deleted for some reason
        if not path.parent.exists():
            path.parent.mkdir(parents = True, exist_ok = True)

        super().reopenIfNeeded()


def createFileHandler(path: Path) -> FileHandler:
    """
        Creates a handler for writting logs to the file system

        Parameters
        ----------
        path : Path
            path of the log file

        Returns
        -------
        FileHandler -> if OS is Windows
        WatchedFileHandler -> if OS is Unix based
    """

    if platform.system() == "Windows":
        return FileHandler(path)

    return CoretexFileHandler(path)
