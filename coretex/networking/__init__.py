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

from .network_manager_base import NetworkManagerBase, RequestFailedError
from .network_manager import networkManager
from .network_object import NetworkObject, DEFAULT_PAGE_SIZE
from .network_response import NetworkResponse, NetworkRequestError
from .request_type import RequestType
from .chunk_upload_session import ChunkUploadSession, MAX_CHUNK_SIZE, fileChunkUpload
from .file_data import FileData
