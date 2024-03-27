from typing import Dict, Any, List, Tuple

import json

from .process import command, CommandException


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


def containerRunning(name: str) -> bool:
    try:
        _, output, _ = command(["docker", "ps", "--format", "{{.Names}}"], ignoreStderr = True, ignoreStdout = True)
        return name in output
    except:
        return False


def containerExists(name: str) -> bool:
    try:
        _, output, _ = command(["docker", "ps", "-a", "--format", "{{.Names}}"], ignoreStderr = True, ignoreStdout = True)
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
    command(["docker", "image", "pull", image])


def start(
    name: str,
    image: str,
    allowGpu: bool,
    ram: int,
    swap: int,
    shm: int,
    cpuCount: int,
    environ: Dict[str, str],
    volumes: List[Tuple[str, str]]
) -> None:

    runCommand = [
        "docker", "run", "-d",
        "--restart", 'always',
        "-p", "21000:21000",
        "--cap-add", "SYS_PTRACE",
        "--network", name,
        "--memory", f"{ram}G",
        "--memory-swap", f"{swap}G",
        "--shm-size", f"{shm}G",
        "--cpus", f"{cpuCount}",
        "--name", name,
    ]

    for key, value in environ.items():
        runCommand.extend(["--env", f"{key}={value}"])

    for source, destination in volumes:
        runCommand.extend(["-v", f"{source}:{destination}"])

    if allowGpu:
        runCommand.extend(["--gpus", "all"])

    # Docker image must always be the last parameter of docker run command
    runCommand.append(image)
    command(runCommand, ignoreStdout = True, ignoreStderr = True)


def stopContainer(name: str) -> None:
    command(["docker", "stop", name], ignoreStdout = True, ignoreStderr = True)


def removeContainer(name: str) -> None:
    command(["docker", "rm", name], ignoreStdout = True, ignoreStderr = True)


def manifestInspect(image: str) -> Dict[str, Any]:
    _, output, _ = command(["docker", "manifest", "inspect", image, "--verbose"], ignoreStdout = True)
    jsonOutput = json.loads(output)
    if not isinstance(jsonOutput, dict):
        raise TypeError(f"Invalid function result type \"{type(jsonOutput)}\". Expected: \"dict\"")

    return jsonOutput


def imageInspect(image: str) -> Dict[str, Any]:
    _, output, _ = command(["docker", "image", "inspect", image], ignoreStdout = True, ignoreStderr = True)
    jsonOutput = json.loads(output)
    if not isinstance(jsonOutput, list):
        raise TypeError(f"Invalid json.loads() result type \"{type(jsonOutput)}\". Expected: \"list\"")

    if not isinstance(jsonOutput[0], dict):  # Since we are inspecting image with specific repository AND tag output will be a list with single object
        raise TypeError(f"Invalid function result type \"{type(jsonOutput[0])}\". Expected: \"dict\"")

    return jsonOutput[0]
