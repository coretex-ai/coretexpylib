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

# import unittest

# from coretex.networking import networkManager


# class BaseNetworkTest:

#     class Base(unittest.TestCase):

#         @classmethod
#         def setUpClass(cls) -> None:
#             # Authenticates with credentials stored inside the Coretex configuration
#             # Configuration can be created using Coretex CLI
#             response = networkManager.authenticateWithStoredCredentials()
#             if response.hasFailed():
#                 raise RuntimeError(f">> [Coretex] Failed to authenticate")
