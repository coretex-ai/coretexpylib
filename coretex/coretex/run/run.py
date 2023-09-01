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

from typing import Optional, Any, List, Dict, Union, Tuple, TypeVar, Generic
from typing_extensions import Self
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path

import os
import time
import logging
import zipfile
import json

from .artifact import Artifact
from .status import RunStatus
from .metrics import Metric
from .parameters import RunParameter, parseParameters
from .execution_type import ExecutionType
from ..dataset import *
from ..space import SpaceTask
from ... import folder_manager
from ...codable import KeyDescriptor
from ...networking import networkManager, NetworkObject, RequestType, NetworkRequestError, FileData


DatasetType = TypeVar("DatasetType", bound = Dataset)

class Run(NetworkObject, Generic[DatasetType]):

    """
        Represents run entity from Coretex.ai

        Properties
        ----------
        datasetId : int
            id of dataset
        name : str
            name of Run
        description : str
            description of Run
        meta : Dict[str, Any]
            meta data of Run
        status : RunStatus
            status of Run
        spaceId : int
            id of Coretex Space
        spaceName : str
            name of Coretex Space
        spaceTask : SpaceTask
            appropriate space task
        jobId : int
            id of job
        jobName : str
            name of job
        createdById : str
            id of created run
        useCachedEnv : bool
            if True chached env will be used, otherwise new environment will be created
    """

    name: str
    description: str
    meta: Dict[str, Any]
    status: RunStatus
    spaceId: int
    spaceName: str
    spaceTask: SpaceTask
    jobId: int
    jobName: str
    createdById: str
    useCachedEnv: bool
    metrics: List[Metric]

    def __init__(self) -> None:
        super(Run, self).__init__()

        self.metrics = []
        self.__parameters: Dict[str, Any] = {}

    @property
    def parameters(self) -> Dict[str, Any]:
        """
            Returns
            -------
            Dict[str, Any] -> Parameters for Run
        """

        return self.__parameters

    @property
    def jobPath(self) -> Path:
        """
            Returns
            -------
            Path -> Path for Run
        """

        return folder_manager.temp / str(self.id)

    @property
    def dataset(self) -> DatasetType:
        """
            Value of the parameter with name "dataset" assigned to this run

            Returns
            -------
            Dataset object if there was a parameter with name "dataset" entered when the run was started

            Raises
            ------
            ValueError -> if there is not parameter with name "dataset"
        """

        dataset = self.parameters.get("dataset")
        if dataset is None:
            raise ValueError(f">> [Coretex] Run \"{self.id}\" does not have a parameter named \"dataset\"")

        return dataset  # type: ignore

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["status"] = KeyDescriptor("status", RunStatus)
        descriptors["spaceId"] = KeyDescriptor("project_id")
        descriptors["spaceName"] = KeyDescriptor("project_name")
        descriptors["spaceTask"] = KeyDescriptor("project_task", SpaceTask)
        descriptors["projectId"] = KeyDescriptor("sub_project_id")
        descriptors["projectName"] = KeyDescriptor("sub_project_name")

        # private properties of the object should not be encoded
        descriptors["__parameters"] = KeyDescriptor(isEncodable = False)

        return descriptors

    @classmethod
    def _endpoint(cls) -> str:
        return "model-queue"

    def onDecode(self) -> None:
        super().onDecode()

        if self.meta["parameters"] is None:
            self.meta["parameters"] = []

        if not isinstance(self.meta["parameters"], list):
            raise ValueError(">> [Coretex] Invalid parameters")

        parameters = [RunParameter.decode(value) for value in self.meta["parameters"]]
        self.__parameters = parseParameters(parameters, self.spaceTask)

    def updateStatus(
        self,
        status: Optional[RunStatus] = None,
        message: Optional[str] = None,
        notifyServer: bool = True
    ) -> bool:

        """
            Updates Run status, if message parameter is None
            default message value will be used\n
            Some Run statuses do not have default message

            Parameters
            ----------
            status : Optional[RunStatus]
                Status to which the run will be updated to
            message : Optional[str]
                Descriptive message for run status, it is diplayed
                when the status is hovered on the Coretex Web App
            notifyServer : bool
                if True update request will be sent to Coretex.ai

            Example
            -------
            >>> from coretex import ExecutingRun, RunStatus
            \b
            >>> ExecutingRun.current().updateStatus(
                    RunStatus.completedWithSuccess
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
            endpoint = "model-queue/job-status-update"
            response = networkManager.genericJSONRequest(endpoint, RequestType.post, parameters)

            if response.hasFailed():
                logging.getLogger("coretexpylib").error(">> [Coretex] Error while updating run status")

            return not response.hasFailed()

        return True

    def createMetrics(self, metrics: List[Metric]) -> None:
        """
            Creates specified metrics for the run

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
            >>> from coretex import ExecutingRun, MetricType
            \b
            >>> metrics = ExecutingRun.current().createMetrics([
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

        response = networkManager.genericJSONRequest(
            "model-queue/metrics-meta",
            RequestType.post,
            parameters
        )

        if response.hasFailed():
            raise NetworkRequestError(response, ">> [Coretex] Failed to create metrics!")

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
            >>> from coretex import ExecutingRun
            \b
            >>> result = ExecutingRun.current().submitMetrics({
                    "loss": (epoch, logs["loss"]),
                    "accuracy": (epoch, logs["accuracy"]),
                })
            >>> print(result)
            True
        """

        metrics = [{
            "timestamp": time.time(),
            "metric": key,
            "x": value[0],
            "y": value[1]
        } for key, value in metricValues.items()]

        parameters: Dict[str, Any] = {
            "experiment_id": self.id,
            "metrics": metrics
        }

        response = networkManager.genericJSONRequest(
            "model-queue/metrics",
            RequestType.post,
            parameters
        )

        return not response.hasFailed()

    def downloadJob(self) -> bool:
        """
            Downloads job snapshot linked to the run

            Returns
            -------
            bool -> True if job downloaded successfully, False if job download has failed
        """

        zipFilePath = f"{self.jobPath}.zip"

        response = networkManager.genericDownload(
            endpoint=f"workspace/download?model_queue_id={self.id}",
            destination=zipFilePath
        )

        with ZipFile(zipFilePath) as zipFile:
            zipFile.extractall(self.jobPath)

        # remove zip file after extract
        os.unlink(zipFilePath)

        if response.hasFailed():
            logging.getLogger("coretexpylib").info(">> [Coretex] Job download has failed")

        return not response.hasFailed()

    def createArtifact(
        self,
        localFilePath: Union[Path, str],
        remoteFilePath: str,
        mimeType: Optional[str] = None
    ) -> Optional[Artifact]:

        """
            Creates Artifact for the current run on Coretex.ai

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
        jobId: int,
        nodeId: Union[int, str],
        name: Optional[str],
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Self:

        """
            Schedules an run for execution on the specified
            Node on Coretex.ai

            Parameters
            ----------
            jobId : int
                id of job that is being used for starting run
            nodeId : Union[int, str]
                id of node that is being used for starting run
            name : Optional[str]
                name of run (not required)
            description : Optional[str]
                run description (not required)
            parameters : Optional[List[Dict[str, Any]]]
                list of parameters (not required)

            Returns
            -------
            Self -> Run object

            Raises
            ------
            NetworkRequestError -> if the request failed

            Example
            -------
            >>> from coretex import Run
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
                    run = Run.run(
                        jobId = 1023,
                        nodeId = 23,
                        name = "Dummy Custom Run
                        description = "Dummy description",
                        parameters = parameters
                    )

                    print(f"Created run with name: {run.name}")
            >>> except NetworkRequestError:
                    print("Failed to create run")
        """

        if isinstance(nodeId, int):
            nodeId = str(nodeId)

        if parameters is None:
            parameters = []

        response = networkManager.genericJSONRequest("run", RequestType.post, {
            "sub_project_id": jobId,
            "service_id": nodeId,
            "name": name,
            "description": description,
            "execution_type": ExecutionType.remote.value,
            "parameters": parameters
        })

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create run")

        return cls.fetchById(response.json["experiment_ids"][0])

    @classmethod
    def runLocal(
        cls,
        spaceId: int,
        name: Optional[str],
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Self:

        """
            Creates run on Coretex.ai with the provided parameters,
            which will be run on the same machine which created it immidiately
            after running the entry point file of the Job

            Parameters
            ----------
            spaceId : int
                id of space that is being used for starting run
            name : Optional[str]
                name of run (not required)
            description : Optional[str]
                run description (not required)
            parameters : Optional[List[Dict[str, Any]]]
                list of parameters (not required)

            Returns
            -------
            Self -> Run object

            Raises
            ------
            NetworkRequestError -> if the request failed
        """

        if parameters is None:
            parameters = []

        # Create snapshot
        snapshotPath = folder_manager.temp / "snapshot.zip"
        with ZipFile(snapshotPath, "w", ZIP_DEFLATED) as snapshotArchive:
            optionalFiles = [
                Path("./main.py"),
                Path("./main.r"),
                Path("./main.R"),
                Path("./environment.yml"),
                Path("./environment-osx.yml")
            ]

            for optionalFile in optionalFiles:
                if not optionalFile.exists():
                    continue

                snapshotArchive.write(optionalFile, optionalFile.name)

            snapshotArchive.write("requirements.txt")
            snapshotArchive.write("experiment.config")

        files = [
            FileData.createFromPath("file", snapshotPath)
        ]

        response = networkManager.genericUpload("run", files, {
            "project_id": spaceId,
            "name": name,
            "description": description,
            "execution_type": ExecutionType.local.value,
            "parameters": json.dumps(parameters)
        })

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create run")

        return cls.fetchById(response.json["experiment_ids"][0])
