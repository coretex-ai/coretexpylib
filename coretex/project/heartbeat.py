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

from threading import Thread

import time
import logging

from ..coretex import Experiment


class Heartbeat(Thread):

    def __init__(self, experiment: Experiment, heartbeatRate: int = 10):
        super(Heartbeat, self).__init__()

        # Don't wait for this thread to finish once the
        # non daemon threads have exited
        self.setDaemon(True)
        self.setName("Heartbeat")

        if heartbeatRate < 1:
            raise ValueError(">> [Coretex] updateInterval must be expressed as an integer of seconds")

        self.__experiment = experiment
        self.__heartbeatRate = heartbeatRate

    def run(self) -> None:
        while True:
            time.sleep(self.__heartbeatRate)

            logging.getLogger("coretexpylib").debug(">> [Coretex] Heartbeat")

            result = self.__experiment.sendHeartbeat()
            if not result:
                logging.getLogger("coretexpylib").debug(">> [Coretex] Heartbeat failed")
