from typing import Union
from pathlib import Path

import sys
import logging
import runpy

from coretex import _task
from coretex.networking import RequestFailedError


def ipynb2py(notebookPath: Union[Path, str], destinationPath: Union[Path, str]) -> Path:
    """
        Converts Python Notebook (ipynb) to Python Script (py)

        Returns
        -------
        Path -> path to converted script
    """

    from nbconvert import PythonExporter
    import nbformat

    if isinstance(notebookPath, str):
        notebookPath = Path(notebookPath)

    if isinstance(destinationPath, str):
        destinationPath = Path(destinationPath)

    exporter = PythonExporter()  # type: ignore[no-untyped-call]

    with notebookPath.open("r") as file:
        notebook = nbformat.read(file, as_version = 4)  # type: ignore[no-untyped-call]

    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            cell['source'] = '\n'.join(
                line for line in cell['source'].split('\n')
                if not line.strip().startswith('%')
            )

    body, resources = exporter.from_notebook_node(notebook)

    with destinationPath.open("w") as file:
        file.write(body)

    return destinationPath


if __name__ == "__main__":
    taskRunId, callback = _task.processRemote(sys.argv)

    try:
        taskRun = _task._prepareForExecution(taskRunId)
        _task.current_task_run.setCurrentTaskRun(taskRun)

        callback.onStart()

        logging.getLogger("coretexpylib").info(">> [Coretex] TaskRun execution started")

        entryPointPath = Path(taskRun.entryPoint)
        if Path("main.ipynb").exists():
            entryPointPath = Path("main.ipynb")

        if entryPointPath.suffix == ".ipynb":
            entryPointPath = ipynb2py(
                entryPointPath,
                Path.cwd().joinpath(entryPointPath.stem).with_suffix(".py")
            )

        # Run the entry point script
        runpy.run_path(str(entryPointPath), {}, "__main__")

        callback.onSuccess()
    except RequestFailedError:
        callback.onNetworkConnectionLost()
    except KeyboardInterrupt:
        callback.onKeyboardInterrupt()
    except BaseException as ex:
        callback.onException(ex)

        # sys.exit is ok here, finally block is guaranteed to execute
        # due to how sys.exit is implemented (it internally raises SystemExit exception)
        sys.exit(1)
    finally:
        callback.onCleanUp()
