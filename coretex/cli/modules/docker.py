from ...utils import command


def networkExists(name: str) -> bool:
    try:
        _, output, error = command(["docker", "network", "inspect", name], ignoreStdout = True, ignoreStderr = True)
        print(f"o, e : {output, error}")
        return True
    except:
        return False


def createNetwork(name: str) -> None:
    if networkExists(name):
        removeNetwork(name)

    command(["docker", "network", "create", "--driver", "bridge", name])

    # do we handle the case where we have lets say 10 networks with same name but different ids?


def removeNetwork(name: str) -> None:
    command(["docker", "network", "rm", name])


def imagePull(image: str) -> None:
    command(["docker", "image", "pull", image])


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
    command(runCommand)


def stopContainer(name: str) -> None:
    command(["docker", "stop", name])
    command(["docker", "rm", name])


def stop(name: str, networkName: str) -> None:
    stopContainer(name)
    removeNetwork(networkName)
