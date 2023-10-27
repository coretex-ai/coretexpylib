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
