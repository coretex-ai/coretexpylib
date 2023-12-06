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

from typing import Type, TypeVar, Optional, Iterator, Callable, Dict, Any
from contextlib import contextmanager

from .state import DatasetState
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
        Creates a new sequence dataset with the provided name and metadata

        Parameters
        ----------
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
        >>> from coretex import SequenceDataset
        \b
        >>> dummyDataset = SequenceDataset.createSequenceDataset("dummyDataset", 123, pathToMetadata)
        >>> if dummyDataset is not None:
                print("Dataset created successfully")
    """

    try:
        dataset = type_.create(
            name=name,
            project_id=projectId,
            meta=meta)

        if dataset is None:
            raise EntityNotCreated(f">> [Coretex] Failed to create dataset with name: {name}")

        yield dataset
    finally:
        type_.finalizeDatasetState()
