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

# from typing import List, Dict
# from typing_extensions import Self
# from pathlib import Path
# from zipfile import ZipFile

# import json

# from .token import Token
# from ..codable import Codable, KeyDescriptor


# class Transcription(Codable):

#     """
#         Represents a result of a single transcription

#         Properties:
#         text: str -> transcribed text
#         tokens: List[Token] -> tokens of transcribed text
#     """

#     text: str
#     tokens: List[Token]

#     @classmethod
#     def create(cls, text: str, tokens: List[Token]) -> Self:
#         obj = cls()

#         obj.text = text
#         obj.tokens = tokens

#         return obj

#     @classmethod
#     def load(cls, filePath: Path) -> Self:
        # """
        #     Loads saved transcription from a json file

        #     Parameters
        #     ----------
        #     filePath : Path
        #         path to json file

        #     Returns
        #     -------
        #     Self -> loaded transcription
        # """

#         with filePath.open("r") as file:
#             return cls.decode(json.load(file))

#     @classmethod
#     def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
#         descriptors = super()._keyDescriptors()
#         descriptors["tokens"] = KeyDescriptor("tokens", Token, list)

#         return descriptors

#     def save(self, path: Path) -> Path:
        # """
        #     Saves transcription to a zipped json file

        #     Parameters
        #     ----------
        #     path : Path
        #         path to json file

        #     Returns
        #     -------
        #     Path -> path to zip file
        # """

#         with path.open("w") as file:
#             json.dump(self.encode(), file, indent = 4)

#         zipPath = path.parent / f"{path.stem}.zip"

#         with ZipFile(zipPath, "w") as zipFile:
#             zipFile.write(str(path), path.name)

#         return zipPath
