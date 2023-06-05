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

import psutil

from ..metric import Metric


class MetricDiskWrite(Metric):

    def __init__(self) -> None:
        diskIoCounters = psutil.disk_io_counters()

        if diskIoCounters is None:
            self.previousWrittenBytes = 0
        else:
            self.previousWrittenBytes = diskIoCounters.write_bytes

    def extract(self) -> Optional[float]:
        diskIoCounters = psutil.disk_io_counters()
        if diskIoCounters is None:
            return None

        currentWriteBytes = diskIoCounters.write_bytes
        writtenBytesDiff = currentWriteBytes - self.previousWrittenBytes

        self.previousWrittenBytes = currentWriteBytes

        return float(writtenBytesDiff)
