import logging

from coretex.utils import docker
from coretex.cli.modules import node as node_module
from coretex.cli.modules.update import getNodeStatus, NodeStatus
from coretex.configuration import loadConfig


autoUpdateLogger = logging.getLogger("cli-autoupdate")

def updateNode() -> None:
    config = loadConfig()

    if getNodeStatus() != NodeStatus.active:
        autoUpdateLogger.debug("Node is not active!")
        return

    if not node_module.shouldUpdate(config["image"]):
        autoUpdateLogger.debug("Node is already up to date.")
        return

    autoUpdateLogger.debug("Pulling latest image...")
    node_module.pull(config["image"])
    autoUpdateLogger.debug("Latest image successfully pulled!")

    if getNodeStatus() != NodeStatus.active:
        autoUpdateLogger.debug("Node is not active!")
        return

    autoUpdateLogger.debug("Stopping node to perform update...")
    node_module.stop()
    autoUpdateLogger.debug("Node successfully stopped!")

    autoUpdateLogger.debug("Starting node with latest image...")
    node_module.start(config["image"], config)
    autoUpdateLogger.debug("Node successfully started!")

    docker.removeDanglingImages(node_module.getRepoFromImageUrl(config["image"]), node_module.getTagFromImageUrl(config["image"]))


if __name__ == "__main__":
    updateNode()
