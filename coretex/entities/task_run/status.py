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


class TaskRunStatus(IntEnum):

    """
        List of possible TaskRun statuses during the TaskRun lifetime
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
            - preparingToStart : TaskRun preparing to start
            - completedWithSuccess : TaskRun is completed without errors
            - completedWithError : TaskRun is completed with error
            - stopped : TaskRun is stopped manually
            - stopping : TaskRun is stopping

            Returns
            -------
            str -> Appropriate message based on TaskRun status

            Raises
            ------
            ValueError -> if unsupported status is provided
        """

        if self == TaskRunStatus.preparingToStart:
            return "Preparing to start the Task Run."

        if self == TaskRunStatus.completedWithSuccess:
            return "Task Run completed successfully."

        if self == TaskRunStatus.completedWithError:
            return "Task Run failed due to an error. View console output for more details."

        if self == TaskRunStatus.stopped:
            return "User stopped the Task Run."

        if self == TaskRunStatus.stopping:
            return "Stopping the Task Run."

        raise ValueError(f">> [Coretex] {self.name} has no default message")

    @property
    def isFinal(self) -> bool:
        """
            List of final statuses:
            - TaskRunStatus.completedWithSuccess : TaskRun finished without error
            - TaskRunStatus.completedWithError : TaskRun finished with an error
            - TaskRunStatus.stopped : TaskRun is manually stopped

            Returns
            -------
            bool -> True if a status is a final status for a run
        """

        return (
                self == TaskRunStatus.completedWithSuccess or
                self == TaskRunStatus.completedWithError or
                self == TaskRunStatus.stopped
        )
