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

# from typing import Optional
# from pathlib import Path

# from ..coretex import CustomSample
# from ..utils import guessMimeType, InvalidFileExtension


# def getTxtFilePath(sample: CustomSample) -> Optional[Path]:
    # """
    #     Looks for text file in Coretex sample
    #     If extension is .txt file is considered textual

    #     Parameters
    #     ----------
    #     sample : CustomSample
    #         sample to be searched

    #     Returns
    #     -------
    #     Optional[Path] -> first occurence of .txt file if there is any, None otherwise
    # """

#     folderContent = list(sample.load().folderContent)
#     for path in folderContent:
#         if path.suffix == ".txt":
#             return path

#     return None


# def isTxtSample(sample: CustomSample) -> bool:
    # """
    #     Checks whether sample is text sample or not

    #     Parameters
    #     ----------
    #     sample : CustomSample
    #         sample to be checked

    #     Returns
    #     -------
    #     bool -> True if sample is text sample, False otherwise
    # """

#     return getTxtFilePath(sample) is not None


# def getAudioFilePath(sample: CustomSample) -> Optional[Path]:
    # """
    #     Looks for any kind of audio file in Coretex sample
    #     Guesses mime type of the file and looks for any kind of audio mime type

    #     Parameters
    #     ----------
    #     sample : CustomSample
    #         sample to be searched

    #     Returns
    #     -------
    #     Optional[Path] -> first occurence of audio file if there is any, None otherwise
    # """

#     folderContent = list(sample.load().folderContent)
#     for path in folderContent:
#         try:
#             mimeType = guessMimeType(str(path))
#             if "audio" in mimeType:
#                 return path
#         except InvalidFileExtension:
#             continue

#     return None


# def isAudioSample(sample: CustomSample) -> bool:
    # """
    #     Checks whether sample is audio sample or not

    #     Parameters
    #     ----------
    #     sample : CustomSample
    #         sample to be checked

    #     Returns
    #     -------
    #     bool -> True if sample is audio sample, False otherwise
    # """

#     return getAudioFilePath(sample) is not None
