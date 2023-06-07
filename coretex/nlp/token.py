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

# from typing import List, Optional
# from typing_extensions import Self

# from deepspeech import TokenMetadata

# from ..codable import Codable


# class Token(Codable):

#     """
#         Represents a single token from text

#         Properties
#         ----------
#         text : str
#             textual value of the token
#         startIndex : int
#             starting index of the token
#         endIndex : int
#             ending index of the token
#         startTime : Optional[float]
#             starting time of token in audio file
#             (only if token was extracted from audio transcription)
#         endTime : Optional[float]
#             ending time of token in audio file
#             (only if token was extracted from audio transcription)
#     """

#     text: str
#     startIndex: int
#     endIndex: int
#     startTime: Optional[float]
#     endTime: Optional[float]

#     @classmethod
#     def create(
#         cls,
#         text: str,
#         startIndex: int,
#         endIndex: int,
#         startTime: Optional[float],
#         endTime: Optional[float]
#     ) -> Self:

#         obj = cls()

#         obj.text = text
#         obj.startIndex = startIndex
#         obj.endIndex = endIndex
#         obj.startTime = startTime
#         obj.endTime = endTime

#         return obj

#     @classmethod
#     def fromTokenMetadata(cls, tokenMetadata: List[TokenMetadata]) -> List[Self]:
#         """
#             Creates a list of tokens from output of the deepspeech model

#             Parameters
#             ----------
#             tokenMetadata : List[TokenMetadata]
#             output of deepspeech model

#             Returns
#             -------
#             List[Self] -> list of tokens
#         """

#         tokens: List[Self] = []

#         startIndex: Optional[int] = None
#         startTime: Optional[float] = None
#         characters: List[str] = []

#         for currentIndex, element in enumerate(tokenMetadata):
#             if startIndex is None and len(characters) == 0:
#                 startIndex = currentIndex

#             if startTime is None and len(characters) == 0:
#                 startTime = element.start_time

#             if element.text.isspace() and startIndex is not None and startTime is not None and len(characters) > 0:
#                 token = cls.create("".join(characters), startIndex, currentIndex, startTime, element.start_time)
#                 tokens.append(token)

#                 startIndex = None
#                 startTime = None
#                 characters.clear()

#                 continue

#             if not element.text.isspace():
#                 characters.append(element.text)

#         if startIndex is not None and startTime is not None and len(characters) > 0:
#             token = cls.create("".join(characters), startIndex, currentIndex, startTime, element.start_time)
#             tokens.append(token)

#         return tokens

#     @classmethod
#     def fromText(cls, text: str) -> List[Self]:
#         """
#             Tokenizes provided text

#             Parameters:
#             text: str -> text to be tokenized

#             Retursn:
#             List[Self] -> list of tokens
#         """

#         tokens: List[Self] = []

#         startIndex: Optional[int] = None
#         characters: List[str] = []

#         for currentIndex, character in enumerate(text):
#             if startIndex is None and len(characters) == 0:
#                 startIndex = currentIndex

#             if character.isspace() and startIndex is not None and len(characters) > 0:
#                 token = cls.create("".join(characters), startIndex, currentIndex, None, None)
#                 tokens.append(token)

#                 startIndex = None
#                 characters.clear()

#                 continue

#             if not character.isspace():
#                 characters.append(character)

#         if startIndex is not None and len(characters) > 0:
#             token = cls.create("".join(characters), startIndex, currentIndex, None, None)
#             tokens.append(token)

#         return tokens
