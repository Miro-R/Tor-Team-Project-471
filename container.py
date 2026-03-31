import logging
from dataclasses import dataclass

import docker
from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from docker.types import IPAMConfig, IPAMPool

from networking import NetworkInfo

# Enable logging
# TODO: Actually add logging to functions below
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
netLog = logging.getLogger(__name__)

ROUTER_IMAGE = "alpine"
ENV_VARS = None


@dataclass
class BaseContainerInfo:
    docker_container: Container
    name: str
    type: str


@dataclass
class RouterInfo(BaseContainerInfo):
    networks: list[NetworkInfo]


@dataclass
class RelayInfo(BaseContainerInfo):
    relay_type: str  # Guard | Middle | Exit | Directory
    network: NetworkInfo


def _create_star_container(
    client: DockerClient, nets_to_serve: list[NetworkInfo]
) -> RouterInfo:

    router_name = "Star Router"

    star_container = client.containers.create(
        name=router_name,
        image=ROUTER_IMAGE,
        environment=ENV_VARS,
    )

    star_container.exec_run("sysctl -w net.ipv4.ip_forward=1")

    # Connect star router to all networks assigned to each gateway address
    for net_info in nets_to_serve:
        net_info.docker_network.connect(
            container=star_container, ipv4_address=NetworkInfo.gateway
        )

    star_router = RouterInfo(
        docker_container=star_container,
        name=router_name,
        type="router",
        networks=nets_to_serve,
    )

    return star_router


# Create Router Containers
# kwargs for future expansion with different topologies. For now, we will default to a star
def create_router_containers(
    docker_client: DockerClient, nets_to_serve: list[NetworkInfo], connect_type="star"
):

    # Sanity Check if client is initialized
    if not docker_client.ping():
        raise RuntimeError(
            "Unable to create router containers: cannot connect to docker engine!"
        )

    match connect_type:
        case "star":
            container_info = _create_star_container(docker_client, nets_to_serve)
        case _:
            raise ValueError(
                "No other topologies other than star have been implemented at this time"
            )
