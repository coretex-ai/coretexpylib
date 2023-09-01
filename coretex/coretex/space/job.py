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

from typing import Optional, Dict
from typing_extensions import Self

from .base import BaseObject
from ...codable import KeyDescriptor


class Job(BaseObject):

    """
        Represents the job entity from Coretex.ai\n
        Contains properties that describe the job
    """

    isDefault: bool
    jobId: int

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["projectId"] = KeyDescriptor("parentId")

        return descriptors

    @classmethod
    def createJob(cls, name: str, spaceId: int, description: Optional[str]=None) -> Optional[Self]:
        """
            Creates a new job with the provided name and description
            Job is added to the space with provided space id

            Parameters
            ----------
            name : str
                job name
            spaceId : int
                space id the job belongs to
            description : Optional[str]
                job description

            Returns
            -------
            Optional[Self] -> The created job object

            Example
            -------
            >>> from coretex import Job
            \b
            >>> dummyJob = Job.createJob(
                    name = "dummyJob",
                    spaceId = 23,
                    description = "This is dummy job"
                )
            >>> if dummyJob is None:
                    print("Failed to create job")
        """

        return cls.create(parameters={
            "name": name,
            "parent_id": spaceId,
            "description": description
        })
