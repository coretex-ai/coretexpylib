from docker.errors import DockerException, NotFound, APIError

import click
import docker

from ..configuration import loadConfig


SERVICE_CONFIG = {
    "image": "dev.biomechservices.com:5443/coretex-node-dev:latest",
    "environment": {
        "CTX_NODE_NAME": "Neureka",
        "CTX_API_URL": "https://devext.biomechservices.com:29007/",
        "CTX_STORAGE_PATH": "/root/.coretex",
        "CTX_NODE_ACCESS_TOKEN": "800eefbdc8b46c2583475d0699a50c2dbf52ad9e577be2f45e411f664d2dd7a037a8b4e70aed102fa8b6039ec9c4071df7ce628d0bbdbbd3c807d34b57caffbb"
    },
    "name": 'coretex_node',
    "mem_limit": "16G",
    "restart_policy": {"Name": "always"},
    "ports": {"21000": "21000"},
    "extra_hosts": {"dev.biomechservices.com": "192.168.135.10"},
    "cap_add": ["SYS_PTRACE"],
    "network": "coretex_node_gpu",
    "mem_limit": "16gb",
    "memswap_limit": "32g",
    "shm_size": "8gb"
}

@click.command()
def start() -> None:
    try:
        client = docker.from_env()
    except DockerException:
        click.echo("Please make sure you have docker installed on your machine and it is up and running. If that's the case (troubleshoot?)")
        return

    config = loadConfig()

    if config["image"] == "gpu":
        SERVICE_CONFIG["runtime"] = "nvidia"

    SERVICE_CONFIG["environment"]["CTX_NODE_NAME"] = config["nodeName"]
    SERVICE_CONFIG["environment"]["CTX_STORAGE_PATH"] = config["storagePath"]
    SERVICE_CONFIG["environment"]["CTX_NODE_ACCESS_TOKEN"] = config["nodeAccessToken"]
    SERVICE_CONFIG["mem_limit"] = config["nodeRam"]
    SERVICE_CONFIG["memswap_limit"] = config["nodeSwap"]
    SERVICE_CONFIG["shm_size"] = config["nodeSharedMemory"]

    SERVICE_CONFIG["image"] = client.images.pull(SERVICE_CONFIG["image"])

    try:
        client.networks.create(SERVICE_CONFIG["network"], driver = "bridge")
        click.echo(f"Successfully created {SERVICE_CONFIG['network']} network for container.")
    except APIError as e:
        click.echo(f"Error while creating {SERVICE_CONFIG['network']} network for container...")
        return

    container = client.containers.run(detach = True,  **SERVICE_CONFIG)
    if container is not None:
        click.echo(f"Node with name {container.name} started successfully")
        return
    else:
        click.echo("Something went wrong...")
        return

@click.command()
def stop() -> None:
    client = docker.from_env()
    containerName = SERVICE_CONFIG["name"]
    try:
        network = client.networks.get(SERVICE_CONFIG["network"])
        container = client.containers.get(containerName)
        network.disconnect(container)
        container.stop()
        network.remove()
        container.remove()
        click.echo(f"Container {containerName} stopped successfully.")
        return

    except NotFound as e:
        click.echo(f"Container {containerName} not found: {e}")
        return

    except APIError as e:
        click.echo(f"Error occurred while stopping container {containerName}: {e}")
        return


@click.group()
def node() -> None:
    pass

node.add_command(start, "start")
node.add_command(stop, "stop")
