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

from typing import Optional, Any, List, Dict, Union, Tuple, TypeVar, Generic, Type
from typing_extensions import Self, override
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path

import os
import time
import logging
import zipfile
import json

from .utils import createSnapshot
from .artifact import Artifact
from .status import TaskRunStatus
from .metrics import Metric, MetricType
from .parameter import validateParameters, parameter_factory
from .execution_type import ExecutionType
from ..dataset import Dataset, LocalDataset, NetworkDataset
from ..project import ProjectType
from ..model import Model
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import networkManager, NetworkObject, NetworkRequestError, FileData


DatasetType = TypeVar("DatasetType", bound = Dataset)

class TaskRun(NetworkObject, Generic[DatasetType]):

    """
        Represents TaskRun entity from Coretex.ai

        Properties
        ----------
        datasetId : int
            id of dataset
        name : str
            name of TaskRun
        description : str
            description of TaskRun
        meta : Dict[str, Any]
            meta data of TaskRun
        status : TaskRunStatus
            status of TaskRun
        projectId : int
            id of Coretex Project
        projectName : str
            name of Coretex Project
        projectType : ProjectType
            appropriate project type
        taskId : int
            id of task
        taskName : str
            name of task
        createdById : str
            id of created TaskRun
        useCachedEnv : bool
            if True chached env will be used, otherwise new environment will be created
    """

    name: str
    description: str
    meta: Dict[str, Any]
    status: TaskRunStatus
    projectId: int
    projectName: str
    projectType: ProjectType
    taskId: int
    taskName: str
    entryPoint: str
    createdById: str
    useCachedEnv: bool
    executionType: ExecutionType
    metrics: List[Metric]

    def __init__(self) -> None:
        super(TaskRun, self).__init__()

        self.metrics = []
        self.__parameters: Dict[str, Any] = {}

    @property
    def parameters(self) -> Dict[str, Any]:
        """
            Returns
            -------
            Dict[str, Any] -> Parameters for TaskRun
        """

        return self.__parameters

    @property
    def taskPath(self) -> Path:
        """
            Returns
            -------
            Path -> Path for TaskRun
        """

        return folder_manager.temp / str(self.id)

    @property
    def dataset(self) -> DatasetType:
        """
            Value of the parameter with name "dataset" assigned to this TaskRun

            Returns
            -------
            Dataset object if there was a parameter with name "dataset" entered when the TaskRun was started

            Raises
            ------
            ValueError -> if there is not parameter with name "dataset"
        """

        dataset = self.parameters.get("dataset")
        if dataset is None:
            raise ValueError(f">> [Coretex] TaskRun \"{self.id}\" does not have a parameter named \"dataset\"")

        return dataset  # type: ignore

    @property
    def isLocal(self) -> bool:
        return self.executionType == ExecutionType.local

    def setDatasetType(self, datasetType: Type[DatasetType]) -> None:
        for key, value in self.__parameters.items():
            if isinstance(value, LocalDataset) and issubclass(datasetType, LocalDataset):
                self.__parameters[key] = datasetType(value.path)  # type: ignore

            if isinstance(value, NetworkDataset) and issubclass(datasetType, NetworkDataset):
                self.__parameters[key] = datasetType.fetchById(value.id)

    def setModelType(self, modelType: Type[Model]) -> None:
        for key, value in self.__parameters.items():
            if isinstance(value, Model):
                self.__parameters[key] = modelType.fetchById(value.id)

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["status"] = KeyDescriptor("status", TaskRunStatus)
        descriptors["projectId"] = KeyDescriptor("project_id")
        descriptors["projectName"] = KeyDescriptor("project_name")
        descriptors["projectType"] = KeyDescriptor("project_task", ProjectType)
        descriptors["taskId"] = KeyDescriptor("sub_project_id")
        descriptors["taskName"] = KeyDescriptor("sub_project_name")
        descriptors["executionType"] = KeyDescriptor("execution_type", ExecutionType)

        # private properties of the object should not be encoded
        descriptors["__parameters"] = KeyDescriptor(isEncodable = False)

        return descriptors

    @classmethod
    @override
    def _endpoint(cls) -> str:
        return "model-queue"

    @override
    def entityUrl(self) -> str:
        return f"run?id={self.id}"

    def onDecode(self) -> None:
        super().onDecode()

        if self.meta["parameters"] is None:
            self.meta["parameters"] = []

        if not isinstance(self.meta["parameters"], list):
            raise ValueError(">> [Coretex] Invalid parameters")

        parameters = [parameter_factory.create(value) for value in self.meta["parameters"]]

        parameterValidationResults = validateParameters(parameters, verbose = True)
        if not all(parameterValidationResults.values()):
            raise ValueError("Invalid parameters found")

        self.__parameters = {parameter.name: parameter.parseValue(self.projectType) for parameter in parameters}

    def _isInterval(self, metricName: str) -> bool:
        for metric in self.metrics:
            if metric.name == metricName and metric.xType == MetricType.interval.name:
                return True

        return False

    def updateStatus(
        self,
        status: Optional[TaskRunStatus] = None,
        message: Optional[str] = None,
        notifyServer: bool = True
    ) -> bool:

        """
            Updates TaskRun status, if message parameter is None
            default message value will be used\n
            Some TaskRun statuses do not have default message

            Parameters
            ----------
            status : Optional[TaskRunStatus]
                Status to which the TaskRun will be updated to
            message : Optional[str]
                Descriptive message for TaskRun status, it is diplayed
                when the status is hovered on the Coretex Web App
            notifyServer : bool
                if True update request will be sent to Coretex.ai

            Example
            -------
            >>> from coretex import ExecutingTaskRun, TaskRunStatus
            \b
            >>> ExecutingTaskRun.current().updateStatus(
                    TaskRunStatus.completedWithSuccess
                )
            True
        """

        if status is not None:
            self.status = status

        if notifyServer:
            if status is not None and message is None:
                message = status.defaultMessage

            parameters: Dict[str, Any] = {
                "id": self.id
            }

            if status is not None:
                parameters["status"] = status

            if message is not None:
                parameters["message"] = message

            # TODO: Should API rename this too?
            endpoint = f"{self._endpoint()}/job-status-update"
            response = networkManager.post(endpoint, parameters)

            if response.hasFailed():
                logging.getLogger("coretexpylib").error(">> [Coretex] Error while updating TaskRun status")
            elif status is not None:
                logging.getLogger("coretexpylib").info(f">> [Coretex] Updated Task Run status to \"{status.name}\"")

            return not response.hasFailed()

        return True

    def createMetrics(self, metrics: List[Metric]) -> None:
        """
            Creates specified metrics for the TaskRun

            Parameters
            ----------
            values : List[Metric]]
                List of Metric meta objects in this format
                Metric("name", "x_label", "x_type", "y_label", "y_type", "x_range", "y_range")

            Returns
            -------
            List[Metric] -> List of Metric objects

            Raises
            ------
            NetworkRequestError -> if the request failed

            Example
            -------
            >>> from coretex import ExecutingTaskRun, MetricType
            \b
            >>> metrics = ExecutingTaskRun.current().createMetrics([
                    Metric.create("loss", "epoch", MetricType.int, "value", MetricType.float, None, [0, 100]),
                    Metric.create("accuracy", "epoch", MetricType.int, "value", MetricType.float, None, [0, 100])
                ])
            >>> if len(metrics) == 0:
                    print("Failed to create metrics")
        """

        parameters: Dict[str, Any] = {
            "experiment_id": self.id,
            "metrics": [metric.encode() for metric in metrics]
        }

        response = networkManager.post(f"{self._endpoint()}/metrics-meta", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create metrics")

        self.metrics.extend(metrics)

    def submitMetrics(self, metricValues: Dict[str, Tuple[float, float]]) -> bool:
        """
            Appends metric values for the provided metrics

            Parameters
            ----------
            metricValues : Dict[str, Tuple[float, float]]
                Values of metrics in this format {"name": x, y}

            Example
            -------
            >>> from coretex import ExecutingTaskRun
            \b
            >>> result = ExecutingTaskRun.current().submitMetrics({
                    "loss": (epoch, logs["loss"]),
                    "accuracy": (epoch, logs["accuracy"]),
                })
            >>> print(result)
            True
        """

        metrics = [{
            "timestamp": value[0] if self._isInterval(key) else time.time(),
            "metric": key,
            "x": value[0],
            "y": value[1]
        } for key, value in metricValues.items()]

        parameters: Dict[str, Any] = {
            "experiment_id": self.id,
            "metrics": metrics
        }

        response = networkManager.post(f"{self._endpoint()}/metrics", parameters)
        return not response.hasFailed()

    def submitOutput(self, parameterName: str, value: Any) -> None:
        """
            Submit an output of this task to act as a parameter in tasks
            downstream in the Workflow

            Parameters
            ----------
            parameterName : str
                name of the parameter
            value : Any
                value that will be sent (id of the object will be sent
                in case Coretex objects like CustomDataset, Model etc. is submited)

            Raises
            ------
            NetworkRequestError -> if the request failed

            Example
            -------
            >>> from coretex import TaskRun
            \b
            >>> ExecutingTaskRun.current().submitOutputParameter(
                    parameterName = "outputDataset"
                    value = outputDataset
                )
        """

        self.submitOutputs({parameterName: value})

    def submitOutputs(self, outputs: Dict[str, Any]) -> None:
        """
            Submit multiple outputs of this task to act as parameters in tasks
            downstream in the Workflow

            Parameters
            ----------
            outputs : Dict[str, Any]
                dictionary with outputs, with key being the name of the parameter
                (id of the object will be sent in case Coretex objects like
                CustomDataset, Model etc. is submited)

            Raises
            ------
            NetworkRequestError -> if the request failed

            Example
            -------
            >>> from coretex import TaskRun
            \b
            >>> result = ExecutingTaskRun.current().submitOutputParameters({
                    "outputDataset": outputDataset,
                    "numbers": 123
                })
        """

        outputParameters: List[Dict[str, Any]] = []

        for key, value in outputs.items():
            if isinstance(value, NetworkObject):
                value = value.id

            outputParameters.append({key: value})

        parameters: Dict[str, Any] = {
            "id": self.id,
            "parameters": outputParameters
        }

        response = networkManager.post(f"{self._endpoint()}/output-parameter", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, ">> [Coretex] Failed to submit outputs")

    def downloadTask(self) -> bool:
        """
            Downloads task snapshot linked to the TaskRun

            Returns
            -------
            bool -> True if task downloaded successfully, False if task download has failed
        """

        params = {
            "model_queue_id": self.id
        }

        zipFilePath = f"{self.taskPath}.zip"
        response = networkManager.download(f"workspace/download", zipFilePath, params)

        if response.hasFailed():
            logging.getLogger("coretexpylib").info(">> [Coretex] Task download has failed")
            return False

        with ZipFile(zipFilePath) as zipFile:
            zipFile.extractall(self.taskPath)

        # remove zip file after extract
        os.unlink(zipFilePath)

        return not response.hasFailed()

    def createArtifact(
        self,
        localFilePath: Union[Path, str],
        remoteFilePath: str,
        mimeType: Optional[str] = None
    ) -> Optional[Artifact]:

        """
            Creates Artifact for the current TaskRun on Coretex.ai

            Parameters
            ----------
            localFilePath : Union[Path, str]
                local path of Artifact file
            remoteFilePath : str
                path of Artifact file on Coretex
            mimeType : Optional[str]
                mimeType (not required) if not passed guesMimeType() function is used

            Returns
            -------
            Optional[Artifact] -> if response is True returns Artifact object, None otherwise
        """

        return Artifact.create(self.id, localFilePath, remoteFilePath, mimeType)

    def createQiimeArtifact(self, rootArtifactFolderName: str, qiimeArtifactPath: Path) -> None:
        if not zipfile.is_zipfile(qiimeArtifactPath):
            raise ValueError(">> [Coretex] Not an archive")

        localFilePath = str(qiimeArtifactPath)
        remoteFilePath = f"{rootArtifactFolderName}/{qiimeArtifactPath.name}"

        mimeType: Optional[str] = None
        if qiimeArtifactPath.suffix in [".qza", ".qzv"]:
            mimeType = "application/zip"

        artifact = self.createArtifact(localFilePath, remoteFilePath, mimeType)
        if artifact is None:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to upload {localFilePath} to {remoteFilePath}")

        # TODO: Enable when uploading file by file is not slow anymore
        # tempDir = Path(FolderManager.instance().createTempFolder(rootArtifactFolderName))
        # fileUtils.recursiveUnzip(qiimeArtifactPath, tempDir, remove = False)

        # for path in fileUtils.walk(tempDir):
        #     relative = path.relative_to(tempDir)

        #     localFilePath = str(path)
        #     remoteFilePath = f"{rootArtifactFolderName}/{str(relative)}"

        #     logging.getLogger("coretexpylib").debug(f">> [Coretex] Uploading {localFilePath} to {remoteFilePath}")

        #     artifact = self.createArtifact(localFilePath, remoteFilePath)
        #     if artifact is None:
        #         logging.getLogger("coretexpylib").warning(f">> [Coretex] Failed to upload {localFilePath} to {remoteFilePath}")

    @classmethod
    def run(
        cls,
        taskId: int,
        nodeId: Union[int, str],
        name: Optional[str],
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Self:

        """
            Schedules an TaskRun for execution on the specified
            Node on Coretex.ai

            Parameters
            ----------
            taskId : int
                id of task that is being used for starting TaskRun
            nodeId : Union[int, str]
                id of node that is being used for starting TaskRun
            name : Optional[str]
                name of TaskRun (not required)
            description : Optional[str]
                TaskRun description (not required)
            parameters : Optional[List[Dict[str, Any]]]
                list of parameters (not required)

            Returns
            -------
            Self -> TaskRun object

            Raises
            ------
            NetworkRequestError -> if the request failed

            Example
            -------
            >>> from coretex import TaskRun
            >>> from coretex.networking import NetworkRequestError
            \b
            >>> parameters = [
                    {
                        "name": "dataset",
                        "description": "Dataset id that is used for fetching dataset from coretex.",
                        "value": null,
                        "data_type": "dataset",
                        "required": true
                    }
                ]
            \b
            >>> try:
                    taskRun = TaskRun.run(
                        taskId = 1023,
                        nodeId = 23,
                        name = "Dummy Custom TaskRun
                        description = "Dummy description",
                        parameters = parameters
                    )

                    print(f"Created TaskRun with name: {taskRun.name}")
            >>> except NetworkRequestError:
                    print("Failed to create TaskRun")
        """

        if isinstance(nodeId, int):
            nodeId = str(nodeId)

        if parameters is None:
            parameters = []

        response = networkManager.post("run", {
            "sub_project_id": taskId,
            "service_id": nodeId,
            "name": name,
            "description": description,
            "execution_type": ExecutionType.remote.value,
            "parameters": parameters
        })

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create TaskRun")

        responseJson = response.getJson(dict)
        return cls.fetchById(responseJson["experiment_ids"][0])

    @classmethod
    def runLocal(
        cls,
        projectId: int,
        saveSnapshot: bool,
        name: Optional[str],
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        entryPoint: Optional[str] = None
    ) -> Self:

        """
            Creates TaskRun on Coretex.ai with the provided parameters,
            which will be run on the same machine which created it immidiately
            after running the entry point file of the task

            Parameters
            ----------
            projectId : int
                id of project that is being used for starting TaskRun
            saveSnapshot : bool
                true if snapshot of local files will be saved to Coretex
            name : Optional[str]
                name of TaskRun (not required)
            description : Optional[str]
                TaskRun description (not required)
            parameters : Optional[List[Dict[str, Any]]]
                list of parameters (not required)
            entryPoint : Optional[str]
                relative path to the script inside of the project

            Returns
            -------
            Self -> TaskRun object

            Raises
            ------
            NetworkRequestError -> if the request failed
        """

        if parameters is None:
            parameters = []

        params = {
            "project_id": projectId,
            "name": name,
            "description": description,
            "execution_type": ExecutionType.local.value,
            "parameters": json.dumps(parameters)
        }

        if entryPoint is not None:
            params["entry_point"] = entryPoint

        # Create snapshot
        if saveSnapshot:
            files = [FileData.createFromPath("file", createSnapshot())]
        else:
            files = None

        response = networkManager.formData("run", params, files)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create TaskRun")

        responseJson = response.getJson(dict)
        return cls.fetchById(responseJson["experiment_ids"][0])


    def generateEntityName(self) -> str:
        """
            Combines the id and the name of the task run into a name for enitites like
            datasets or models.

            Returns
            -------
            str -> the generated name
        """

        name = f"{self.id}-{self.name}"
        return name[:50]
