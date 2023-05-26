import logging

import psutil

from ..metric import Metric


class MetricSwapUsage(Metric):

    def extract(self) -> float:
        swapPercentage = psutil.swap_memory().percent
        if swapPercentage >= 90:
            logging.getLogger("coretexpylib").warning(f">> [Coretex] Swap memory usage is at {swapPercentage}")

        return swapPercentage
