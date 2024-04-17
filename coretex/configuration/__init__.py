from .user import UserConfiguration, LoginInfo
from .node import NodeConfiguration
from .base import CONFIG_DIR


def _syncConfigWithEnv() -> None:
    # If configuration doesn't exist default one will be created
    # Initialization of User and Node Configuration classes will do
    # the necessary sync between config properties and corresponding
    # environment variables (e.g. storagePath -> CTX_STORAGE_PATH)

    UserConfiguration()
    NodeConfiguration()
