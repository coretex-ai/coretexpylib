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

from typing import Tuple

import time

import psutil


def getNetworkUsage() -> Tuple[float, float]:
    netIOCounters1 = psutil.net_io_counters(pernic=True)
    time.sleep(1)
    netIOCounters2 = psutil.net_io_counters(pernic=True)

    totalBytesRecv = 0
    totalBytesSent = 0

    for interface, counters1 in netIOCounters1.items():
        counters2 = netIOCounters2[interface]

        bytesRecv = counters2.bytes_recv - counters1.bytes_recv
        bytesSent = counters2.bytes_sent - counters1.bytes_sent

        totalBytesRecv += bytesRecv
        totalBytesSent += bytesSent

    return float(totalBytesRecv * 8), float(totalBytesSent * 8)
