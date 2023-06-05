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

# from .token import Token
# from .transcription import Transcription
# from .utils import getTxtFilePath
# from ..coretex import CustomSample


# def loadTxtSample(sample: CustomSample) -> Transcription:
#     """
#         Tokenizes text sample

#         Parameters
#         ----------
#         sample : CustomSample
#         sample to be tokenized

#         Returns
#         -------
#         Transcription -> text and a list of tokens contained in the text

#         Raises
#         ------
#         ValueError -> if provided sample is not a valid text sample
#     """

#     path = getTxtFilePath(sample)
#     if path is None:
#         raise ValueError(f">> [Coretex] {sample.name} does not contain a valid txt file")

#     with path.open("r") as txtFile:
#         text = "\n".join(txtFile.readlines()).strip()

#     return Transcription.create(text, Token.fromText(text))
