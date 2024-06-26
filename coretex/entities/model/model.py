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

from typing import Any, Dict, Union, Optional
from typing_extensions import Self, override
from datetime import datetime
from zipfile import ZipFile
from pathlib import Path

import json
import logging

from ..utils import isEntityNameValid
from ... import folder_manager
from ...networking import networkManager, NetworkObject, ChunkUploadSession, MAX_CHUNK_SIZE, NetworkRequestError
from ...codable import KeyDescriptor


class Model(NetworkObject):

    """
        Represents a machine learning model object on Coretex.ai
        Contains properties that describe the model

        Properties
        ----------
        name : str
            model name
        createdById : str
            id of model
        createdOn : datetime
            date of model creation
        datasetId : int
            dataset id that is used for training the model
        projectId : int
            project id that is used for training the model
        taskId : int
            task id that is used for training the model
        isTrained : bool
            True if model is trained, False otherwise
        isDeleted : bool
            True if model is deleted, False otherwise
        accuracy : float
            model accuracy
        taskRunId : int
            TaskRun id of trained model
        meta : Dict[str, Any]
            model meta data
    """

    name: str
    createdById: str
    createdOn: datetime
    datasetId: int
    projectId: int
    taskId: int
    isTrained: bool
    isDeleted: bool
    accuracy: float
    taskRunId: int
    meta: Dict[str, Any]

    @property
    def path(self) -> Path:
        return folder_manager.modelsFolder / str(self.id)

    @property
    def zipPath(self) -> Path:
        return self.path.with_suffix(".zip")

    @classmethod
    def modelDescriptorFileName(cls) -> str:
        """
            Returns
            -------
            str -> name of model descriptor file
        """

        return "model_descriptor.json"

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["taskRunId"] = KeyDescriptor("model_queue_id")

        return descriptors

    @classmethod
    def createModel(
        cls,
        name: str,
        taskRunId: int,
        accuracy: float,
        meta: Optional[Dict[str, Any]] = None
    ) -> Self:

        """
            Creates Model as a result of TaskRun

            Parameters
            ----------
            name : str
                model name
            taskRunId : int
                TaskRun id of model
            accuracy : float
                model accuracy
            meta : Optional[Dict[str, Any]]
                model metadata

            Returns
            -------
            Self -> Model object

            Raises
            -------
            NetworkRequestError -> If model creation failed

            Example
            -------
            >>> from coretex import Model, currentTaskRun
            >>> model = Model.createModel("model-name", currentTaskRun().id, 0.87)
        """

        if not isEntityNameValid(name):
            raise ValueError(">> [Coretex] Model name is invalid. Requirements: alphanumeric characters (\"a-z\", and \"0-9\") and dash (\"-\") with length between 3 to 50")

        if accuracy < 0:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Invalid value for accuracy: ({accuracy} < 0), clipping to 0.")

        if accuracy > 1:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Invalid value for accuracy: ({accuracy} > 1), clipping to 1.")

        accuracy = max(0, min(accuracy, 1))

        if meta is None:
            meta = {}

        return cls.create(
            name = name,
            model_queue_id = taskRunId,
            accuracy = accuracy,
            meta = meta
        )

    @classmethod
    def createProjectModel(
        cls,
        name: str,
        projectId: int,
        accuracy: float,
        meta: Optional[Dict[str, Any]] = None
    ) -> Self:

        """
            Creates Model object inside of the provided Project with specified properties

            Parameters
            ----------
            name : str
                Model name
            projectId : int
                Project to which the Model will be added
            accuracy : float
                Model accuracy
            meta : Dict[str, Any]
                Model metadata

            Returns
            -------
            Self -> Model object

            Example
            -------
            >>> from coretex import Model
            >>> model = Model.createProjectModel("model-name", 123, 0.87)
        """

        if meta is None:
            meta = {}

        return cls.create(
            name = name,
            project_id = projectId,
            accuracy = accuracy,
            meta = meta
        )

    @classmethod
    def saveModelDescriptor(cls, path: Union[Path, str], contents: Dict[str, Any]) -> None:
        """
            Saves a model descriptor - a JSON file that provides a description of a
            machine learning model. It includes information such as the model's
            architecture, input and output shapes, labels, description and etc.

            Parameters
            ----------
            path : Union[Path, str]
                path to where the model descriptor will be saved
            contents : Dict[str, Any]
                key-value pairs which will be stored as json

            Example
            -------
            >>> from coretex import currentTaskRun, Model
            >>> model = Model.createModel("model-name", currentTaskRun().id, accuracy)
            >>> model.saveModelDescriptor(modelPath, {
                    "project_task": currentTaskRun().projectType,
                    "labels": labels,
                    "modelName": model.name,
                    "description": currentTaskRun().description,

                    "input_description":
                        Input shape is [x, y]

                        x is actually number of samples in dataset\n
                        y represents number of unique taxons for selected level in dataset,

                    "input_shape": [x, y],

                    "output_description":
                        Output shape - [x, z]

                        x is actually number of samples in dataset\n
                        z represents that output 2d array (table) is going to have only 1 column (1 prediction for each sample in dataset),

                    "output_shape": [x, z]
                })
        """

        if isinstance(path, str):
            path = Path(path)

        modelDescriptorPath = path / cls.modelDescriptorFileName()

        with modelDescriptorPath.open("w", encoding = "utf-8") as file:
            json.dump(contents, file, ensure_ascii = False, indent = 4)

    @override
    def entityUrl(self) -> str:
        return f'model-item?id={self.id}'

    def download(self, path: Optional[Path] = None, ignoreCache: bool = False) -> None:
        """
            Downloads and extracts the model zip file from Coretex.ai
        """

        if path is None:
            path = self.path

        if self.isDeleted or not self.isTrained:
            return

        if path.exists() and not ignoreCache:
            return

        modelZip = path.with_suffix(".zip")
        response = networkManager.download(f"{self._endpoint()}/download", modelZip, {
            "id": self.id
        })

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to download Model")

        with ZipFile(modelZip) as zipFile:
            zipFile.extractall(path)

    def upload(self, path: Union[Path, str]) -> None:
        """
            Uploads the provided model folder as zip file to Coretex.ai

            Parameters
            ----------
            path : Union[Path, str]
                Path to the model directory

            Raises
            -------
            ValueError -> if provided path is not a directory
            NetworkRequestError -> if Model upload failed

            Example
            -------
            >>> from coretex import Model, currentTaskRun
            >>> model = Model.createModel("model-name", currentTaskRun().id, 0.87)
            >>> model.upload("path/to/model-dir")
        """

        if isinstance(path, str):
            path = Path(path)

        if not path.is_dir():
            raise ValueError("\"path\" must be a directory")

        zipPath = path.with_suffix(".zip")
        with ZipFile(zipPath, "w") as zipFile:
            for value in path.rglob("*"):
                if not value.is_file():
                    continue

                zipFile.write(value, value.relative_to(path))

        uploadSession = ChunkUploadSession(MAX_CHUNK_SIZE, zipPath)
        uploadId = uploadSession.run()

        parameters = {
            "id": self.id,
            "file_id": uploadId
        }

        response = networkManager.formData("model/upload", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to upload model")
