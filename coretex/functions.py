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

from typing import Optional, Any, Dict


def badRequest(error: str) -> Dict[str, Any]:
    """
        Creates a json object for bad request

        Parameters
        ----------
        error : str
            Error message

        Returns
        -------
        dict -> Json object for bad request
    """

    return {
        "code": 400,
        "body": {
            "error": error
        }
    }


def success(data: Optional[Any] = None) -> Dict[str, Any]:
    """
        Creates a json object for successful request

        Parameters
        ----------
        data : Optional[Any]
            Response data

        Returns
        -------
        dict -> Json object for successful request
    """

    if data is None:
        data = {}

    return {
        "code": 200,
        "body": data
    }
