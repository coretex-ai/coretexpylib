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

from typing import Optional

from .network_response import NetworkResponse
from .network_manager_base import NetworkManagerBase
from ..configuration import UserConfiguration


class NetworkManager(NetworkManagerBase):

    """
        Subclass of NetworkManagerBase intended to be used
        by a normal user. Contains functionality related to user
        and authenticating as a normal user.
    """

    def __init__(self) -> None:
        super().__init__()

        self._userApiToken: Optional[str] = None
        self._userRefreshToken: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None

        try:
            userConfig = UserConfiguration.load()
            self._userApiToken = userConfig.token
            self._userRefreshToken = userConfig.refreshToken
            self._username = userConfig.username
            self._password = userConfig.password
        except:
            pass

    @property
    def _apiToken(self) -> Optional[str]:
        return self._userApiToken

    @_apiToken.setter
    def _apiToken(self, value: Optional[str]) -> None:
        self._userApiToken = value

    @property
    def _refreshToken(self) -> Optional[str]:
        return self._userRefreshToken

    @_refreshToken.setter
    def _refreshToken(self, value: Optional[str]) -> None:
        self._userRefreshToken = value

    @property
    def hasStoredCredentials(self) -> bool:
        return self._username is not None and self._password is not None

    def authenticate(self, username: str, password: str, storeCredentials: bool = True) -> NetworkResponse:
        """
            Authenticates user with provided credentials

            Parameters
            ----------
            username : str
                Coretex.ai username
            password : str
                Coretex.ai password
            storeCredentials : bool
                If true credentials will be stored in User object for reuse

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Example
            -------
            >>> from coretex.networking import networkManager
            \b
            >>> response = networkManager.authenticate(username = "dummy@coretex.ai", password = "123456")
            >>> if response.hasFailed():
                    print("Failed to authenticate")
        """

        if storeCredentials:
            self._username = username
            self._password = password

        # authenticate using credentials stored in requests.Session.auth
        return super().authenticate(username, password, storeCredentials)

    def authenticateWithStoredCredentials(self) -> NetworkResponse:
        """
            Authenticates user with credentials stored inside User object

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Raises
            ------
            ValueError -> if credentials are not found
        """

        if self._username is None or self._password is None:
            raise ValueError(">> [Coretex] Credentials not stored")

        return self.authenticate(self._username, self._password)


networkManager: NetworkManagerBase = NetworkManager()
