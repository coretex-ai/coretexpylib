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

from typing import Dict, Any

from .type import SecretType
from .secret import Secret
from .aws_secret import AWSSecret
from .git_secret import GitSecret
from .credentials import CredentialsSecret


def create(value: Dict[str, Any]) -> Secret:
    rawType = value.get("type_")
    if rawType is None:
        raise ValueError("Invalid Secret json received. \"type_\" field missing")

    del value["type_"]
    type_ = SecretType(rawType)

    if type_ == SecretType.aws:
        return AWSSecret.decode(value)

    if type_ == SecretType.git:
        return GitSecret.decode(value)

    if type_ == SecretType.credentials:
        return CredentialsSecret.decode(value)
