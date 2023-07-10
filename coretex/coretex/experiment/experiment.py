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

from typing import Final, Optional, Any, List, Dict, Union, Tuple, TypeVar, Generic
from typing_extensions import Self
from threading import Lock
from zipfile import ZipFile
from pathlib import Path

import os
import time
import logging
import zipfile

from .artifact import Artifact
from .status import ExperimentStatus
from .metrics import Metric
from .parameters import ExperimentParameter, parseParameters
from ..dataset import *
from ..space import SpaceTask
from ...codable import KeyDescriptor
from ...networking import networkManager, NetworkObject, RequestType, NetworkRequestError
from ...folder_management import FolderManager


DatasetType = TypeVar("DatasetType", bound = Dataset)

class Experiment(NetworkObject, Generic[DatasetType]):

    """
        Represents experiment entity from Coretex.ai

        Properties
        ----------
        datasetId : int
            id of dataset
        name : str
            name of Experiment
        description : str
            description of Experiment
        meta : Dict[str, Any]
            meta data of Experiment
        status : ExperimentStatus
            status of Experiment
        spaceId : int
            id of Coretex Space
        spaceName : str
            name of Coretex Space
        spaceTask : SpaceTask
            appropriate space task
        projectId : int
            id of project
        projectName : str
            name of project
        createdById : str
            id of created experiment
        useCachedEnv : bool
            if True chached env will be used, otherwise new environment will be created
    """

    name: str
    description: str
    meta: Dict[str, Any]
    status: ExperimentStatus
    spaceId: int
    spaceName: str
    spaceTask: SpaceTask
    projectId: int
    projectName: str
    createdById: str
    useCachedEnv: bool
    metrics: List[Metric]

    def __init__(self) -> None:
        super(Experiment, self).__init__()

        self.metrics = []
        self.__parameters: Dict[str, Any] = {}

    @property
    def parameters(self) -> Dict[str, Any]:
        """
            Returns
            -------
            Dict[str, Any] -> Parameters for Experiment
        """

        return self.__parameters

    @property
    def projectPath(self) -> str:
        """
            Returns
            -------
            str -> Path for Experiment
        """

        return FolderManager.instance().getTempFolder(str(self.id))

    @property
    def dataset(self) -> DatasetType:
        """
            Value of the parameter with name "dataset" assigned to this experiment

            Returns
            -------
            Dataset object if there was a parameter with name "dataset" entered when the experiment was started

            Raises
            ------
            ValueError -> if there is not parameter with name "dataset"
        """

        dataset = self.parameters.get("dataset")
        if dataset is None:
            raise ValueError(f">> [Coretex] Experiment \"{self.id}\" does not have a parameter named \"dataset\"")

        return dataset  # type: ignore

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()

        descriptors["status"] = KeyDescriptor("status", ExperimentStatus)
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

        parameters = [ExperimentParameter.decode(value) for value in self.meta["parameters"]]
        self.__parameters = parseParameters(parameters, self.spaceTask)

    def updateStatus(
        self,
        status: Optional[ExperimentStatus] = None,
        message: Optional[str] = None,
        notifyServer: bool = True
    ) -> bool:

        """
            Updates Experiment status, if message parameter is None
            default message value will be used\n
            Some Experiment statuses do not have default message

            Parameters
            ----------
            status : Optional[ExperimentStatus]
                Status to which the experiment will be updated to
            message : Optional[str]
                Descriptive message for experiment status, it is diplayed
                when the status is hovered on the Coretex Web App
            notifyServer : bool
                if True update request will be sent to Coretex.ai

            Example
            -------
            >>> from coretex import ExecutingExperiment, ExperimentStatus
            \b
            >>> ExecutingExperiment.current().updateStatus(
                    ExperimentStatus.completedWithSuccess
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
                logging.getLogger("coretexpylib").error(">> [Coretex] Error while updating experiment status")

            return not response.hasFailed()

        return True

    def createMetrics(self, metrics: List[Metric]) -> None:
        """
            Creates specified metrics for the experiment

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
            >>> from coretex import ExecutingExperiment, MetricType
            \b
            >>> metrics = ExecutingExperiment.current().createMetrics([
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
            >>> from coretex import ExecutingExperiment
            \b
            >>> result = ExecutingExperiment.current().submitMetrics({
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

    def downloadProject(self) -> bool:
        """
            Downloads project snapshot linked to the experiment

            Returns
            -------
            bool -> True if project downloaded successfully, False if project download has failed
        """

        zipFilePath = f"{self.projectPath}.zip"

        response = networkManager.genericDownload(
            endpoint=f"workspace/download?model_queue_id={self.id}",
            destination=zipFilePath
        )

        with ZipFile(zipFilePath) as zipFile:
            zipFile.extractall(self.projectPath)

        # remove zip file after extract
        os.unlink(zipFilePath)

        if response.hasFailed():
            logging.getLogger("coretexpylib").info(">> [Coretex] Project download has failed")

        return not response.hasFailed()

    def createArtifact(self, localFilePath: str, remoteFilePath: str, mimeType: Optional[str] = None) -> Optional[Artifact]:
        """
            Creates Artifact for the current Experiment on Coretex.ai

            Parameters
            ----------
            localFilePath : str
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
        projectId: int,
        nodeId: Union[int, str],
        name: Optional[str],
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Self:
        """
            Starts an Experiment on Coretex.ai with the provided parameters

            Parameters
            ----------
            projectId : int
                id of project that is being used for starting custom Experiment
            nodeId : Union[int, str]
                id of node that is being used for starting custom Experiment
            name : Optional[str]
                name of Experiment
            description : Optional[str]
                Experiment description (not required)
            parameters : Optional[List[Dict[str, Any]]]
                list of parameters (not required)

            Returns
            -------
            Self -> Experiment object

            Raises
            ------
            NetworkRequestError -> if the request failed

            Example
            -------
            >>> from coretex import Experiment
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
                    experiment = Experiment.run(
                        projectId = 1023,
                        nodeId = 23,
                        name = "Dummy Custom Experiment
                        description = "Dummy description",
                        parameters = parameters
                    )

                    print(f"Created experiment with name: {experiment.name}")
            >>> except NetworkRequestError:
                    print("Failed to create experiment")
        """

        if isinstance(nodeId, int):
            nodeId = str(nodeId)

        if parameters is None:
            parameters = []

        response = networkManager.genericJSONRequest("run", RequestType.post, {
            "sub_project_id": projectId,
            "service_id": nodeId,
            "name": name,
            "description": description,
            "parameters": parameters
        })

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create experiment")

        return cls.decode(response.json[0])
