from .base import CONFIG_DIR
from .user import UserConfiguration, LoginInfo
from .node import NodeConfiguration


def _syncConfigWithEnv() -> None:
    # TODO: explain this !
    print("sync")
    UserConfiguration()
    NodeConfiguration()
