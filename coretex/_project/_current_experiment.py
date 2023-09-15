from typing import Optional

from ..coretex import TaskRun


class _CurrentTaskRunContainer:

    taskRun: Optional[TaskRun] = None


def setCurrentTaskRun(taskRun: Optional[TaskRun]) -> None:
    _CurrentTaskRunContainer.taskRun = taskRun


def currentTaskRun() -> TaskRun:
    taskRun = _CurrentTaskRunContainer.taskRun
    if taskRun is None:
        raise ValueError("TaskRun is not currently executing")

    return taskRun
