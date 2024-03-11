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

from datetime import datetime, timezone


# Time zone used for dates on Coretex backend
TIME_ZONE = timezone.utc

# Date format used by Coretex backend
DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f%z"

CORETEX_DATE_FORMATS = [
    DATE_FORMAT,
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z"
]


def decodeDate(value: str) -> datetime:
    """
        Converts the date to a format used by Coretex

        Returns
        -------
        datetime -> object whose datetime is represented using the Coretex datetime format
    """

    for format in CORETEX_DATE_FORMATS:
        try:
            return datetime.strptime(value, format)
        except ValueError:
            continue

    for format in CORETEX_DATE_FORMATS:
        try:
            # Python's datetime library requires UTC minutes to always
            # be present in the date in either of those 2 formats:
            # - +HHMM
            # - +HH:MM
            # BUT coretex API sends it in one of those formats:
            # - +HH
            # - +HH:MM (only if the minutes have actual value)
            # so we need to handle the first case where minutes
            # are not present by adding them manually
            return datetime.strptime(f"{value}00", format)
        except ValueError:
            continue

    raise ValueError(f"Failed to convert \"{value}\" to any of the supported formats \"{CORETEX_DATE_FORMATS}\"")
