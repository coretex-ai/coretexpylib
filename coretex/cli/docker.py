from ..utils import command


class DockerException(Exception):

    """
        Exception which is raised due to any unexpected behaviour with docker module
    """

    pass


def createNetwork(name: str) -> None:
    command(["docker", "network", "create", "--driver", "bridge", name])


def removeNetwork(name: str) -> None:
    command(["docker", "network", "rm", name])


def runNode(
    name: str,
    dockerImage: str,
    imageType: str,
    serverUrl: str,
    storagePath: str,
    nodeAccessToken: str,
    nodeRam: str,
    nodeSwap: str,
    nodeSharedMemory: str,
    restartPolicy: str,
    ports: str,
    capAdd: str,
) -> None:

    runCommand = [
        "docker", "run", "-d",
        "--env", f"CTX_API_URL={serverUrl}",
        "--env", f"CTX_STORAGE_PATH={storagePath}",
        "--env", f"CTX_NODE_ACCESS_TOKEN={nodeAccessToken}",
        "--restart", restartPolicy,
        "-p", ports,
        "--cap-add", capAdd,
        "--network", name,
        "--memory", nodeRam,
        "--memory-swap", nodeSwap,
        "--shm-size", nodeSharedMemory,
        "--name", name,
    ]

    if imageType == "gpu":
        runCommand.extend(["--gpus", "all"])

    runCommand.append(dockerImage)
    command(runCommand)


def stopContainer(name: str) -> None:
    command(["docker", "stop", name])
    command(["docker", "rm", name])


def stopNode(name: str, networkName: str) -> None:
    stopContainer(name)
    removeNetwork(networkName)
