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

from enum import IntEnum


class RunStatus(IntEnum):

    """
        List of possible run statuses during the run lifetime
    """

    queued = 1
    preparingToStart = 2
    inProgress = 3
    completedWithSuccess = 4
    completedWithError = 5
    stopped = 6
    stopping = 7
    startRequested = 8
    stopRequested = 9

    @property
    def defaultMessage(self) -> str:
        """
            List of supported statuses:
            - preparingToStart : run preparing to start
            - completedWithSuccess : run is completed without errors
            - completedWithError : run is completed with error
            - stopped : run is stopped manually
            - stopping : run is stopping

            Returns
            -------
            str -> Appropriate message based on run status

            Raises
            ------
            ValueError -> if unsupported status is provided
        """

        if self == RunStatus.preparingToStart:
            return "Preparing to start the run."

        if self == RunStatus.completedWithSuccess:
            return "Run completed successfully."

        if self == RunStatus.completedWithError:
            return "Run execution was interrupted due to an error. View run console for more details."

        if self == RunStatus.stopped:
            return "Run execution was stopped by request from the user."

        if self == RunStatus.stopping:
            return "Stopping the run."

        raise ValueError(f">> [Coretex] {self.name} has no default message")

    @property
    def isFinal(self) -> bool:
        """
            List of final statuses:
            - RunStatus.completedWithSuccess : Run finished without error
            - RunStatus.completedWithError : Run finished with an error
            - RunStatus.stopped : Run is manually stopped

            Returns
            -------
            bool -> True if a status is a final status for a run
        """

        return (
                self == RunStatus.completedWithSuccess or
                self == RunStatus.completedWithError or
                self == RunStatus.stopped
        )
