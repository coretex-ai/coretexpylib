import subprocess


class DockerException(Exception):

    """
        Exception which is raised due to any unexpected behaviour with docker module
    """

    pass


def createNetwork(name: str) -> None:
    try:
        subprocess.run(["docker", "network", "create", "--driver", "bridge", name], check=True)
    except:
        raise DockerException(f"Failed to create network: {name}")


def removeNetwork(name: str) -> None:
    try:
        subprocess.run(["docker", "network", "rm", name], check = True)
    except:
        raise DockerException(f"Failed to remove network: {name}")


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
    ) -> bool:

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

    subprocess.run(runCommand, check=True)

    # Check if the container is running
    containerRunning = subprocess.run(["docker", "inspect", "--format", "{{.State.Running}}", name], capture_output=True, text=True).stdout.strip()

    if containerRunning == "true":
        return True

    return False


def stopContainer(name: str) -> None:
    try:
        # Disconnect and stop the container
        subprocess.run(["docker", "stop", name], check=True)

        # Remove the container
        subprocess.run(["docker", "rm", name], check=True)
    except:
        raise DockerException(f"Failed to stop container {name}.")


def stopNode(name: str, networkName: str) -> bool:
    try:
        stopContainer(name)

        removeNetwork(networkName)

        return True
    except:
        raise DockerException(f"Error occurred while stopping container {name}.")
