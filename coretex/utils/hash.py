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

import base64
import hashlib


MAX_NAME_LENGTH = 50


def hashCacheName(name: str, suffix: str) -> str:
    if MAX_NAME_LENGTH - len(name) < 8:
        raise ValueError(">> [Coretex] Failed to cache dataset. Dataset name too long")

    suffixByteHash = hashlib.md5(suffix.encode()).digest()
    suffixHash = base64.b64encode(suffixByteHash)
    cacheName = name + "-" + suffixHash.decode("ascii")
    cacheName = cacheName.lower()
    cacheName = cacheName.replace("+", "0")
    cacheName = cacheName.replace("/", "0")
    cacheName = cacheName.replace("=", "0")

    return cacheName[:MAX_NAME_LENGTH] if len(cacheName) > MAX_NAME_LENGTH else cacheName
