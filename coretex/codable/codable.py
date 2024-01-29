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

from typing import Any, Optional, Type, Dict, Tuple
from typing_extensions import Self
from datetime import datetime
from enum import Enum
from uuid import UUID

import inflection

from .descriptor import KeyDescriptor
from ..utils.date import DATE_FORMAT, decodeDate


class Codable:

    """
        Class whose subclasses can be serialized/deserialized into/from a JSON format object
    """

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        """
            Defines a custom mapping for python objects to json field
            Key of the dictionary represents a name of the field in python
            Value of the dictionary represents how should the object be serialized/deserialized

            Returns
            -------
            Dict[str, KeyDescriptor] -> Dictionary of objects describing translation
        """

        return {}

    @classmethod
    def __keyDescriptorByJsonName(cls, jsonName: str) -> Tuple[Optional[str], Optional[KeyDescriptor]]:
        for key, value in cls._keyDescriptors().items():
            if value.jsonName == jsonName:
                return key, value

        return None, None

    @classmethod
    def __keyDescriptorByPythonName(cls, pythonName: str) -> Optional[KeyDescriptor]:
        if not pythonName in cls._keyDescriptors().keys():
            return None

        return cls._keyDescriptors()[pythonName]

    # - Encoding

    def __encodeKey(self, key: str) -> str:
        descriptor = self.__class__.__keyDescriptorByPythonName(key)

        if descriptor is None or descriptor.jsonName is None:
            return inflection.underscore(key)

        return descriptor.jsonName

    def _encodeValue(self, key: str, value: Any) -> Any:
        """
            Encodes python value into a json property
            Custom field serialization can be implemented by overriding this method

            Parameters
            ----------
            key : str
                python object variable name
            value : Any
                json object represented as an object from standard python library

            Returns
            -------
            Any -> encoded value of the object
        """

        descriptor = self.__class__.__keyDescriptorByPythonName(key)

        if descriptor is None or descriptor.pythonType is None:
            return value

        if issubclass(descriptor.pythonType, Enum):
            if descriptor.isList():
                return [element.value for element in value]

            return value.value

        if issubclass(descriptor.pythonType, UUID):
            if descriptor.isList():
                return [str(element) for element in value]

            return str(value)

        if issubclass(descriptor.pythonType, Codable):
            if descriptor.isList():
                return [descriptor.pythonType.encode(element) for element in value]

            return descriptor.pythonType.encode(value)

        if issubclass(descriptor.pythonType, datetime):
            if descriptor.isList():
                return [element.strftime(DATE_FORMAT) for element in value]

            return value.strftime(DATE_FORMAT)

        return value

    def encode(self) -> Dict[str, Any]:
        """
            Encodes python object into dictionary which contains
            only values representable by standard python library/types

            Returns
            -------
            Dict[str, Any] -> encoded object which can be serialized into json string
        """

        encodedObject: Dict[str, Any] = {}

        for key, value in self.__dict__.items():
            descriptor = self.__class__.__keyDescriptorByPythonName(key)

            # skip ignored fields for encoding
            if descriptor is not None and not descriptor.isEncodable:
                # print(f">> [Coretex] Skipping encoding for field: {key}")
                continue

            encodedKey = self.__encodeKey(key)
            encodedValue = self._encodeValue(key, value)

            encodedObject[encodedKey] = encodedValue

        return encodedObject

    # - Decoding

    @classmethod
    def __decodeKey(cls, key: str) -> str:
        descriptorKey, _ = cls.__keyDescriptorByJsonName(key)

        if descriptorKey is None:
            return inflection.camelize(key, False)

        return descriptorKey

    @classmethod
    def _decodeValue(cls, key: str, value: Any) -> Any:
        """
            Decodes a value of a single json field
            Custom logic can be implemented by overriding this method

            Parameters
            ----------
            key : str
                name of the json field
            value : Any
                value of the json field

            Returns
            -------
            Any -> decoded value of the json field
        """

        _, descriptor = cls.__keyDescriptorByJsonName(key)

        if descriptor is None or descriptor.pythonType is None:
            return value

        if issubclass(descriptor.pythonType, Enum):
            if descriptor.isList() and descriptor.collectionType is not None:
                return descriptor.collectionType([descriptor.pythonType(element) for element in value])

            return descriptor.pythonType(value)

        if issubclass(descriptor.pythonType, UUID):
            if descriptor.isList() and descriptor.collectionType is not None:
                return descriptor.collectionType([descriptor.pythonType(element) for element in value])

            return descriptor.pythonType(value)

        if issubclass(descriptor.pythonType, Codable):
            if descriptor.isList() and descriptor.collectionType is not None:
                return descriptor.collectionType([descriptor.pythonType.decode(element) for element in value])

            return descriptor.pythonType.decode(value)

        if issubclass(descriptor.pythonType, datetime):
            if descriptor.isList() and descriptor.collectionType is not None:
                return descriptor.collectionType([decodeDate(element) for element in value])

            return decodeDate(value)

        return value

    def _updateFields(self, encodedObject: Dict[str, Any]) -> None:
        """
            Updates the properties of object with new values

            Parameters
            ----------
            encodedObject : Dict[str, Any]
                json encoded object
        """

        for key, value in encodedObject.items():
            _, descriptor = self.__class__.__keyDescriptorByJsonName(key)

            # skip ignored fields for deserialization
            if descriptor is not None and not descriptor.isDecodable:
                # print(f">> [Coretex] Skipping decoding for field: {key}")
                continue

            decodedKey = self.__decodeKey(key)
            self.__dict__[decodedKey] = self._decodeValue(key, value)

    def onDecode(self) -> None:
        """
            Callback which is called once the object has been decoded
        """

        pass

    @classmethod
    def decode(cls, encodedObject: Dict[str, Any]) -> Self:
        """
            Decodes the json object into a python object

            Parameters
            ----------
            encodedObject : Dict[str, Any]
                json encoded object

            Returns
            -------
            Self -> Decoded python object
        """
        obj = cls()

        obj._updateFields(encodedObject)
        obj.onDecode()

        return obj
