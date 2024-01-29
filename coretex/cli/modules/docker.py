from ...utils import command


def checkDockerAvailability() -> None:
    try:
        # Run the command to check if Docker existing and running
        command(["docker", "ps"], ignoreStdout = True)
    except Exception as ex:
        if "not found" in str(ex):
            raise RuntimeError("It seems that Docker is not installed on your machine or it is not configured properly. Please make sure Docker is installed and properly configured to proceed.")

        if "docker ps" in str(ex):
            raise RuntimeError("It seems that Docker isn't running on your machine right now. Please ensure Docker is up and running to proceed.")

        else:
            raise RuntimeError(f"Something went wrong. {ex}")


def networkExists(name: str) -> bool:
    try:
        command(["docker", "network", "inspect", name], ignoreStdout = True, ignoreStderr = True)
        return True
    except:
        return False


def createNetwork(name: str) -> None:
    if networkExists(name):
        removeNetwork(name)

    command(["docker", "network", "create", "--driver", "bridge", name], ignoreStdout = True)

    # do we handle the case where we have lets say 10 networks with same name but different ids?


def removeNetwork(name: str) -> None:
    command(["docker", "network", "rm", name], ignoreStdout = True, ignoreStderr = True)


def imagePull(image: str) -> None:
    command(["docker", "image", "pull", image], ignoreStdout = True)


def start(
    name: str,
    dockerImage: str,
    imageType: str,
    serverUrl: str,
    storagePath: str,
    nodeAccessToken: str,
    nodeRam: str,
    nodeSwap: str,
    nodeSharedMemory: str,
) -> None:

    runCommand = [
        "docker", "run", "-d",
        "--env", f"CTX_API_URL={serverUrl}",
        "--env", f"CTX_STORAGE_PATH={storagePath}",
        "--env", f"CTX_NODE_ACCESS_TOKEN={nodeAccessToken}",
        "--restart", 'always',
        "-p", "21000:21000",
        "--cap-add", "SYS_PTRACE",
        "--network", name,
        "--memory", f"{nodeRam}G",
        "--memory-swap", f"{nodeSwap}G",
        "--shm-size", f"{nodeSharedMemory}G",
        "--name", name,
    ]

    if imageType == "gpu":
        runCommand.extend(["--gpus", "all"])

    runCommand.append(dockerImage)
    command(runCommand, ignoreStdout = True)


def stopContainer(name: str) -> None:
    command(["docker", "stop", name], ignoreStdout = True)
    command(["docker", "rm", name], ignoreStdout = True)


def stop(name: str, networkName: str) -> None:
    stopContainer(name)
    removeNetwork(networkName)
