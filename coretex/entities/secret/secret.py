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

from typing import Any, Dict, Optional, Tuple
from typing_extensions import Self
from abc import ABC, abstractmethod
from base64 import b64decode

import copy

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from .type import SecretType
from ...networking import NetworkObject, networkManager, NetworkRequestError, RequestType
from ...cryptography import rsa


class Secret(NetworkObject, ABC):

    """
        Represents base Secret entity from Coretex.ai
    """

    def __init__(self, type_: SecretType) -> None:
        super().__init__()

        self.type_ = type_

    @abstractmethod
    def _encryptedFields(self) -> Tuple[str, ...]:
        """
            Returns
            -------
            Tuple[str, ...] -> A list of fields which are to be
                decrypted when "Secret.decrypted" is called
        """

        pass

    def decrypted(self, key: Optional[RSAPrivateKey] = None) -> Self:
        """
            Returns
            -------
            Self -> Decrypted Coretex Secret
        """

        if key is None:
            key = rsa.getPrivateKey()

        decrypted = copy.deepcopy(self)

        for field in self._encryptedFields():
            if not field in decrypted.__dict__:
                raise AttributeError(f"\"{type(decrypted)}\".\"{field}\" not found")

            value = decrypted.__dict__[field]
            if not isinstance(value, str):
                raise TypeError(f"Expected \"str\" received \"{type(value)}\"")

            decrypted.__dict__[field] = rsa.decrypt(key, b64decode(value)).decode("utf-8")

        return decrypted

    @classmethod
    def _endpoint(cls) -> str:
        return "secret"

    def refresh(self, jsonObject: Optional[Dict[str, Any]] = None) -> bool:
        """
            Secret does not support this method
        """

        return NotImplemented

    def update(self, **kwargs: Any) -> bool:
        """
            Secret does not support this method
        """

        return NotImplemented

    @classmethod
    def fetchById(cls, objectId: int, **kwargs: Any) -> Self:
        """
            Secret does not support this method
        """

        return NotImplemented

    @classmethod
    def fetchByName(cls, name: str) -> Self:
        """
            Fetches a single Secret with the matching name

            Parameters
            ----------
            name : str
                name of the Secret which is fetched

            Returns
            -------
            Self -> fetched Secret

            Raises
            ------
            NetworkRequestError -> If the request for fetching failed
        """

        response = networkManager.get(f"{cls._endpoint()}/data", {
            "name": name
        })

        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to fetch Secret \"{name}\"")

        return cls.decode(response.getJson(dict))

    @classmethod
    def fetchNodeSecret(cls, name: str, accessToken: str) -> Self:
        """
            Fetches a single Node Secret with the matching name

            Parameters
            ----------
            name : str
                name of the Node Secret which is fetched
            accessToken : str
                Node access token

            Returns
            -------
            Self -> fetched Node Secret

            Raises
            ------
            NetworkRequestError -> If the request for fetching failed
        """

        headers = networkManager._headers()
        headers["node-access-token"] = accessToken

        response = networkManager.request("secret/node", RequestType.get, headers, {
            "name": name
        })

        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to fetch Node Secret \"{name}\"")

        return cls.decode(response.getJson(dict))
