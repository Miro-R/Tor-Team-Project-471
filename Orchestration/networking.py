# networking.py - initializes networks and routers

import ipaddress
import logging
from dataclasses import dataclass
from sqlite3.dbapi2 import connect

from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from docker.types import IPAMConfig, IPAMPool

from container import ContainerInfo
from tor_sim_consts import BASE_SUBNET, PROJECT_LABEL, RUN_LABEL
from tor_types import ContainerInfo, NetworkInfo

# Enable logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
netLog = logging.getLogger(__name__)

# generate subnets
# TODO: investigate potential issue of subnet fragmentation (when subsub evenly divisable by base) making
# addressing calculations invalid


# TODO: restructure this to dynamically check subnets as they're being generated
def _gen_subnets(
    num_networks: int, subsubnet_prefix: int
) -> list[tuple[str, ipaddress.IPv4Network]]:
    # Sanity checks
    # Check base_subnet validity
    try:
        base = ipaddress.IPv4Network(BASE_SUBNET, strict=True)
    except ValueError as e:
        raise ValueError(f"Invalid (IPv4) subnet '{BASE_SUBNET}': {e}")
    if num_networks <= 0:
        raise ValueError(f"num_networks must be a positive integer, got {num_networks}")

    if not base.is_private:
        raise ValueError(f"base subnet {BASE_SUBNET} must be private!")

    # check if base_subnet can accomidate num_networks specified
    base_maxaddress = base.num_addresses
    subsub_maxaddress = 2 ** (base.max_prefixlen - subsubnet_prefix)
    total_subsub_address = num_networks * subsub_maxaddress

    if base_maxaddress < total_subsub_address:
        raise ValueError(
            f"Base subnet {BASE_SUBNET} cannot accomidate {num_networks} networks!"
        )

    netLog.debug(
        f"Base_subnet {BASE_SUBNET} successfully validated against having {num_networks} with prefix {subsubnet_prefix}"
    )

    # Actual generation starts here
    # Generate network names (overriding first and last network for Client and Server, respectively)
    try:
        base.subnets(new_prefix=subsubnet_prefix)
    except Exception as e:
        raise Exception(f"An unknown error occurred: {e}")

    subsubnet_tuple = zip(
        [f"{PROJECT_LABEL}-{RUN_LABEL}-net{i}" for i in range(num_networks)],
        list(base.subnets(new_prefix=subsubnet_prefix)),
    )

    return list(subsubnet_tuple)


def _create_router(
    client: DockerClient,
    connect_to: list[NetworkInfo],
) -> ContainerInfo:

    # Set the router ip to be one before the broadcast address (255 - 1 = 254)
    name = "central-router"
    # Harcode this for now
    image = "debian:stable-slim"
    docker_container = client.containers.run(
        image=image,
        name=name,
        labels={
            "simulation.project": PROJECT_LABEL,
            "simulation.run": RUN_LABEL,
        },
        privileged=True,
        command=[
            "sh",
            "-c",
            "echo 1 > /proc/sys/net/ipv4/ip_forward && sleep infinity",
        ],
        detach=True,
    )

    netLog.info(f"Created {name}")

    # Connect to specified IP
    for net in connect_to:
        router_ip = str(ipaddress.IPv4Network(net.subnet).broadcast_address - 1)
        net.docker_network.connect(name, ipv4_address=router_ip)
        netLog.info(f"Router connected at {router_ip}")

    return ContainerInfo(
        docker_container=docker_container,
        name=name,
        image=image,
    )


# FUTURE: selectable spawn strategy (randomized subnet start, sequential, fibonacci idk)
def create_docker_networks(
    client: DockerClient, num_networks: int, subsubnet_prefix: int
) -> list[NetworkInfo]:

    # generate subnets
    subsubnet_tuple = _gen_subnets(num_networks, subsubnet_prefix)
    base = ipaddress.ip_network(BASE_SUBNET)

    # Assert that the docker service is running
    if not client.ping():
        raise RuntimeError("networking.py: client unable to reach docker!")

    # create docker networks
    docker_networks = [
        client.networks.create(
            subsubnet[0],
            driver="bridge",
            labels={
                "simulation.project": PROJECT_LABEL,
                "simulation.run": RUN_LABEL,
            },
            ipam=IPAMConfig(
                pool_configs=[
                    IPAMPool(
                        subnet=str(subsubnet[1]),
                    )
                ]
            ),
        )
        for subsubnet in subsubnet_tuple
    ]

    # construct and return NetworkInfo instances
    ni_list = list()

    ni_list = [
        NetworkInfo(
            docker_network=net,
            name=name,
            subnet=str(subnet),
            gateway=str(subnet.broadcast_address - 1),
        )
        for net, (name, subnet) in zip(docker_networks, subsubnet_tuple)
    ]

    # Create router for each network instance at gateway
    _create_router(client, ni_list)

    return ni_list


if __name__ == "__main__":
    netLog.error("networking.py is not a standalone script!")
    exit(1)
