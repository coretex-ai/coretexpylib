from typing import Dict, Any

import json

from ...utils import command, CommandException


def isDockerAvailable() -> None:
    try:
        # Run the command to check if Docker exists and is available
        command(["docker", "ps"], ignoreStdout = True, ignoreStderr = True)
    except CommandException:
        raise RuntimeError("Docker not available. Please check that it is properly installed and running on your system.")


def networkExists(name: str) -> bool:
    # This function inspects the specified Docker network using the
    # 'docker network inspect' command. If the command exits with a return code
    # of 0, indicating success, the function returns True, meaning the network exists.
    # If the command exits with a non-zero return code, indicating failure,
    # the function returns False, meaning the network doesn't exist.
    try:
        command(["docker", "network", "inspect", name], ignoreStdout = True, ignoreStderr = True)
        return True
    except:
        return False


def containerExists(name: str) -> bool:
    try:
        _, output, _ = command(["docker", "ps", "--format", "{{.Names}}"], ignoreStderr = True, ignoreStdout = True)
        return name in output
    except:
        return False


def createNetwork(name: str) -> None:
    if networkExists(name):
        removeNetwork(name)

    command(["docker", "network", "create", "--driver", "bridge", name], ignoreStdout = True)


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
    nodeRam: int,
    nodeSwap: int,
    nodeSharedMemory: int,
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
    command(["docker", "stop", name], ignoreStdout = True, ignoreStderr = True)
    command(["docker", "rm", name], ignoreStdout = True, ignoreStderr = True)


def stop(name: str, networkName: str) -> None:
    stopContainer(name)
    removeNetwork(networkName)


def manifestInspect(repository: str, tag: str) -> Dict[str, Any]:
    _, output, _ = command(["docker", "manifest", "inspect", f"{repository}:{tag}", "--verbose"], ignoreStdout = True)
    jsonOutput = json.loads(output)
    if not isinstance(jsonOutput, dict):
        raise TypeError(f"Invalid function result type \"{type(jsonOutput)}\". Expected: \"dict\"")

    return jsonOutput


def imageInspect(repository: str, tag: str) -> Dict[str, Any]:
    _, output, _ = command(["docker", "image", "inspect", f"{repository}:{tag}"], ignoreStdout = True, ignoreStderr = True)
    jsonOutput = json.loads(output)
    if not isinstance(jsonOutput, list):
        raise TypeError(f"Invalid json.loads() result type \"{type(jsonOutput)}\". Expected: \"list\"")

    if not isinstance(jsonOutput[0], dict):  # Since we are inspecting image with specific repository AND tag output will be a list with single object
        raise TypeError(f"Invalid function result type \"{type(jsonOutput[0])}\". Expected: \"dict\"")

    return jsonOutput[0]
