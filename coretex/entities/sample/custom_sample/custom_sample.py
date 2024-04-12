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

from .custom_sample_data import CustomSampleData
from .local_custom_sample import LocalCustomSample
from ..network_sample import NetworkSample


class CustomSample(NetworkSample[CustomSampleData], LocalCustomSample):

    """
        Represents the custom Sample object from Coretex.ai\n
        Custom samples are used when working with Other Task\n
        Custom sample must be an archive
    """

    def __init__(self) -> None:
        NetworkSample.__init__(self)
