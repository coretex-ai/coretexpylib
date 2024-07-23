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

import os
import logging
import shutil

from py3nvml import py3nvml

import psutil


def getCpuUsage() -> float:
    """
        Returns
        -------
        float -> CPU usage as percentage since last call of this function
    """

    return psutil.cpu_percent()


def getRamUsage() -> float:
    """
        Returns
        -------
        float -> Used RAM memory as percentage
    """

    return psutil.virtual_memory().percent


def getAvailableRam() -> int:
    """
        Returns
        -------
        int -> total RAM memory in GB as int
    """

    memory = psutil.virtual_memory()
    return int(memory.total / (1024 ** 3))


def getAvailableCpuCount() -> int:
    availableCPUs = os.cpu_count()
    return availableCPUs if availableCPUs is not None else 1


def getGpuUsage() -> float:
    """
        py3nvml init must be called before calling this function
        otherwise it will raise an exception

        Returns
        -------
        float -> GPU usage as percentage
    """

    handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
    utilization = py3nvml.nvmlDeviceGetUtilizationRates(handle)

    if isinstance(utilization, py3nvml.c_nvmlUtilization_t):
        return float(utilization.gpu)

    logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to extract gpu usage metric")
    return 0


def getGpuMemoryUsage() -> float:
    """
        py3nvml init must be called before calling this function
        otherwise it will raise an exception

        Returns
        -------
        float -> GPU memory usage as percentage
    """

    handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
    memory = py3nvml.nvmlDeviceGetMemoryInfo(handle)

    if not isinstance(memory, py3nvml.c_nvmlMemory_t):
        logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to extract gpu memory usage metric")
        return 0

    return float(memory.used / memory.total)


def getGpuTemperature() -> float:
    """
        py3nvml init must be called before calling this function
        otherwise it will raise an exception

        Returns
        -------
        float -> GPU temperature
    """

    handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
    temperature = py3nvml.nvmlDeviceGetTemperature(handle, py3nvml.NVML_TEMPERATURE_GPU)

    return float(temperature)


def getSwapUsage() -> float:
    """
        Returns
        -------
        float -> Used swap memory as percentage
    """

    return psutil.swap_memory().percent


def getTotalSwapMemory() -> int:
    """
        Returns
        -------
        int -> total swap memory in GB
    """

    return int(psutil.swap_memory().total / (1024 ** 3))


def getDiskRead() -> float:
    """
        Returns
        -------
        float -> total amount of bytes read from disk
    """

    counters = psutil.disk_io_counters()

    if counters is None:
        logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to extract disk read metric")
        return 0

    return float(counters.read_bytes)


def getDiskWrite() -> float:
    """
        Returns
        -------
        float -> total amount of bytes wrote to disk
    """

    counters = psutil.disk_io_counters()

    if counters is None:
        logging.getLogger("coretexpylib").debug(">> [Coretex] Failed to extract disk write metric")
        return 0

    return float(counters.write_bytes)


def getStorageUsage() -> float:
    """
        Returns
        -------
        float -> Used storage space as percentage
    """

    info = shutil.disk_usage("/")
    return info.used / info.total * 100  # 0-1 range -> 0-100 range


def _getNetworkUsage() -> Tuple[float, float]:
    counters = psutil.net_io_counters(pernic = True)

    totalBytesRecv = 0
    totalBytesSent = 0

    for counter in counters.values():
        bytesRecv = counter.bytes_recv
        bytesSent = counter.bytes_sent

        totalBytesRecv += bytesRecv
        totalBytesSent += bytesSent

    return float(totalBytesRecv * 8), float(totalBytesSent * 8)


def getDownloadSpeed() -> float:
    """
        Returns
        -------
        float -> total amount of bytes downloaded
    """

    return _getNetworkUsage()[0]


def getUploadSpeed() -> float:
    """
        Returns
        -------
        float -> total amount of bytes uploaded
    """

    return _getNetworkUsage()[1]
