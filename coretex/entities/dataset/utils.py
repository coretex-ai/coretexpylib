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

from typing import Type, TypeVar, Optional, Iterator, Dict, Any
from contextlib import contextmanager

from .network_dataset import EntityNotCreated, NetworkDataset


T = TypeVar("T", bound = NetworkDataset)


@contextmanager
def createDataset(
    type_: Type[T],
    name: str,
    projectId: int,
    meta: Optional[Dict[str, Any]] = None
) -> Iterator[T]:

    """
        Creates a new dataset with the provided name and type
        and finalizes its state in data base

        Parameters
        ----------
        type_ : Type[T]
            type of dataset which will be created
        name : str
            dataset name
        projectId : int
            project for which the dataset will be created
        metadataPath : Union[Path, str]
            path the zipped metadata file

        Returns
        -------
        The created sequence dataset object or None if creation failed

        Example
        -------
        >>> from coretex import createDataset
        \b
        >>> with createDataset("dummyDataset", 123, pathToMetadata) as dataset:
        >>>     print(f"Dataset with id \"{dataset.id}\" and name \"{dataset.name}\" created")
    """

    dataset = type_.create(
        name = name,
        project_id = projectId,
        meta = meta
    )

    if dataset is None:
        raise EntityNotCreated(f">> [Coretex] Failed to create dataset with name \"{name}\" ")

    yield dataset
    if not dataset.finalize():
        raise ValueError(">> [Coretex] Failed to finalize dataset")
