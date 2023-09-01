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

from typing import Any, Dict, Union
from typing_extensions import Self
from datetime import datetime
from zipfile import ZipFile
from pathlib import Path

import json
import logging

from ... import folder_manager
from ...networking import networkManager, NetworkObject, FileData
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
        spaceId : int
            space id that is used for training the model
        jobId : int
            job id that is used for training the model
        isTrained : bool
            True if model is trained, False otherwise
        isDeleted : bool
            True if model is deleted, False otherwise
        accuracy : float
            model accuracy
        runId : int
            run id of trained model
        meta : Dict[str, Any]
            model meta data
    """

    name: str
    createdById: str
    createdOn: datetime
    datasetId: int
    spaceId: int
    jobId: int
    isTrained: bool
    isDeleted: bool
    accuracy: float
    runId: int
    meta: Dict[str, Any]

    @property
    def path(self) -> Path:
        return folder_manager.modelsFolder / str(self.id)

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
        descriptors["experimentId"] = KeyDescriptor("model_queue_id")

        return descriptors

    @classmethod
    def createModel(cls, name: str, runId: int, accuracy: float, meta: Dict[str, Any]) -> Self:
        """
            Creates Model object of the provided run with specified properties

            Parameters
            ----------
            name : str
                model name
            runId : int
                run id of model
            accuracy : float
                model accuracy
            meta : Dict[str, Any]
                model meta data

            Returns
            -------
            Self -> Model object

            Example
            -------
            >>> from coretex import Model, ExecutingRun
            \b
            >>> run = ExecutingRun.current()
            >>> model = Model.createModel(
                    name = run.name,
                    runId = run.id,
                    accuracy = 0.87,
                    meta = {}
                )
        """

        model = cls.create(parameters = {
            "name": name,
            "model_queue_id": runId,
            "accuracy": accuracy,
            "meta": meta
        })

        if model is None:
            raise ValueError(">> [Coretex] Failed to create Model entity")

        return model

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
            >>> from coretex import ExecutingRun, Model
            >>> model = Model.createModel(run.name, run.id, accuracy, {})
            >>> model.saveModelDescriptor(modelPath, {
                    "project_task": run.spaceTask,
                    "labels": labels,
                    "modelName": model.name,
                    "description": run.description,

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

        with open(modelDescriptorPath, "w", encoding = "utf-8") as file:
            json.dump(contents, file, ensure_ascii = False, indent = 4)

    def download(self, ignoreCache: bool = False) -> None:
        """
            Downloads and extracts the model zip file from Coretex.ai
        """

        if self.isDeleted or not self.isTrained:
            return

        if self.path.exists() and not ignoreCache:
            return

        modelZip = folder_manager.modelsFolder / f"{self.id}.zip"
        response = networkManager.genericDownload(f"model/download?id={self.id}", modelZip)

        if response.hasFailed():
            logging.getLogger("coretexpylib").info(">> [Coretex] Failed to download the model")

        with ZipFile(modelZip) as zipFile:
            zipFile.extractall(self.path)

    def upload(self, path: Union[Path, str]) -> bool:
        """
            Uploads the provided model folder as zip file to Coretex.ai

            Parameters
            ----------
            path : Union[Path, str]
                Path to the saved model directory

            Returns
            -------
            bool -> True if model data uploaded successfully, False if model data upload has failed


            Example
            -------
            >>> from coretex import Model, ExecutingRun
            \b
            >>> run: ExecutingRun[NetworkDataset] = ExecutingRun.current()
            >>> model = Model.createModel(
                name = run.name,
                runId = run.id,
                accuracy = 0.87,
                meta = {}
            )
            >>> if not model.upload("path/to/model-dir"):
                    print("Failed to upload model")
        """

        if self.isDeleted:
            return False

        if isinstance(path, str):
            path = Path(path)

        if not path.is_dir():
            raise ValueError(">> [Coretex] \"path\" must be a directory")

        logging.getLogger("coretexpylib").info(">> [Coretex] Uploading model file...")

        zipPath = path.with_suffix(".zip")
        with ZipFile(zipPath, "w") as zipFile:
            for value in path.rglob("*"):
                if not value.is_file():
                    continue

                zipFile.write(value, value.relative_to(path))

        files = [
            FileData.createFromPath("file", zipPath)
        ]

        parameters = {
            "id": self.id
        }

        response = networkManager.genericUpload("model/upload", files, parameters)
        if response.hasFailed():
            logging.getLogger("coretexpylib").info(">> [Coretex] Failed to upload model file")
        else:
            logging.getLogger("coretexpylib").info(">> [Coretex] Uploaded model file")

        return not response.hasFailed()
