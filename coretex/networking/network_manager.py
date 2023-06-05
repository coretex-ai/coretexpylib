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
from .user_data import UserData


class NetworkManager(NetworkManagerBase):

    """
        Subclass of NetworkManagerBase intended to be used
        by a normal user. Contains functionality related to user
        and authenticating as a normal user.
    """

    def __init__(self) -> None:
        super().__init__()

        self.__userData = UserData()

    @property
    def _apiToken(self) -> Optional[str]:
        return self.__userData.apiToken

    @_apiToken.setter
    def _apiToken(self, value: Optional[str]) -> None:
        self.__userData.apiToken = value

    @property
    def _refreshToken(self) -> Optional[str]:
        return self.__userData.refreshToken

    @_refreshToken.setter
    def _refreshToken(self, value: Optional[str]) -> None:
        self.__userData.refreshToken = value

    @property
    def hasStoredCredentials(self) -> bool:
        return self.__userData.hasStoredCredentials

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
            self.__userData.username = username
            self.__userData.password = password

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

        if self.__userData.username is None or self.__userData.password is None:
            raise ValueError(">> [Coretex] Credentials not stored")

        return self.authenticate(self.__userData.username, self.__userData.password)


networkManager: NetworkManagerBase = NetworkManager()
