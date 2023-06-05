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

from typing import Final
from threading import Lock

import sys


class ConsoleProgressBar:

    barLength: int = 30

    def __init__(self, total: int, title: str):
        self.total: Final = total
        self.title: Final = title

        self.__current = 0
        self.__lock = Lock()

    def update(self) -> None:
        with self.__lock:
            self.__current += 1

            currentPct = float(self.__current) * 100.0 / self.total
            progressBar = '=' * int(currentPct / 100 * ConsoleProgressBar.barLength - 1) + '>'
            emptySpace = '.' * (ConsoleProgressBar.barLength - len(progressBar))

            sys.stdout.write("\r")
            sys.stdout.write(">> [Coretex] {0}: [{1}{2}] - {3}%".format(self.title, progressBar, emptySpace, int(round(currentPct))))
            sys.stdout.flush()

    def finish(self) -> None:
        with self.__lock:
            currentPct = 100
            progressBar = "=" * int(currentPct / 100 * ConsoleProgressBar.barLength)
            emptySpace = "." * (ConsoleProgressBar.barLength - len(progressBar))

            sys.stdout.write("\r")
            sys.stdout.write(">> [Coretex] {0}: [{1}{2}] - {3}% - {4}\n".format(self.title, progressBar, emptySpace, int(round(currentPct)), "Finished"))
            sys.stdout.flush()
