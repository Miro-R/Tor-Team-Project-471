# networking.py - initializes networks and routes

import ipaddress
import logging
from dataclasses import dataclass

from docker.client import DockerClient
from docker.models.networks import Network
from docker.types import IPAMConfig, IPAMPool

# Enable logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
netLog = logging.getLogger(__name__)

# generate subnets
# TODO: investigate potential issue of subnet fragmentation (when subsub evenly divisable by base) making
# addressing calculations invalid


@dataclass
class NetworkInfo:
    docker_network: Network
    name: str
    subnet: str
    gateway: str


def _gen_subnets(
    base_subnet: str, num_networks: int, subsubnet_prefix: int
) -> list[tuple[str, ipaddress.IPv4Network | ipaddress.IPv6Network]]:
    # Sanity checks
    # Check base_subnet validity
    try:
        base = ipaddress.ip_network(base_subnet, strict=True)
    except ValueError as e:
        raise ValueError(f"Invalid subnet '{base_subnet}': {e}")

    if num_networks <= 0:
        raise ValueError(f"num_networks must be a positive integer, got {num_networks}")

    if not base.is_private:
        raise ValueError(f"base subnet must be private!")

    # check if base_subnet can accomidate num_networks specified
    base_maxaddress = base.num_addresses
    subsub_maxaddress = 2 ** (base.max_prefixlen - subsubnet_prefix)
    total_subsub_address = num_networks * subsub_maxaddress

    if base_maxaddress < total_subsub_address:
        raise ValueError(
            f"Base subnet {base_subnet} cannot accomidate {num_networks} networks!"
        )

    netLog.debug(
        f"Base_subnet {base_subnet} successfully validated against having {num_networks} with prefix {subsubnet_prefix}"
    )

    # Actual generation starts here
    # Generate network names (overriding first and last network for Client and Server, respectively)
    try:
        base.subnets(new_prefix=subsubnet_prefix)
    except Exception as e:
        raise Exception(f"An unknown error occurred: {e}")

    subsubnet_tuple = zip(
        [f"net{i}" for i in range(num_networks)],
        list(base.subnets(new_prefix=subsubnet_prefix)),
    )

    return list(subsubnet_tuple)


# FUTURE: selectable spawn strategy (randomized subnet start, sequential, fibonacci idk)
def create_docker_networks(
    client: DockerClient, base_subnet: str, num_networks: int, subsubnet_prefix: int
) -> list[NetworkInfo]:

    # generate subnets
    subsubnet_tuple = _gen_subnets(base_subnet, num_networks, subsubnet_prefix)
    base = ipaddress.ip_network(base_subnet)

    # Assert that the docker service is running
    assert client.ping

    # create docker networks
    docker_networks = [
        client.networks.create(
            subsubnet[0],
            driver="bridge",
            ipam=IPAMConfig(
                pool_configs=[
                    IPAMPool(
                        subnet=str(subsubnet[1]),
                        gateway=str(subsubnet[1].network_address + 1),
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
            gateway=str(subnet.network_address + 1),
        )
        for net, (name, subnet) in zip(docker_networks, subsubnet_tuple)
    ]

    return ni_list


if __name__ == "__main__":
    netLog.error("networking.py is not a standalone script!")
    exit(1)
