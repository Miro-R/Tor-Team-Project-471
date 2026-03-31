import logging
import time
from dataclasses import dataclass

from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from docker.types import IPAMConfig, IPAMPool

import tor_sim_consts
from container import BaseContainerInfo
from networking import NetworkInfo

# Enable logging
# TODO: Actually add logging to functions below
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
router_log = logging.getLogger(__name__)

ROUTER_IMAGE = "alpine"
ENV_VARS = None


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

    router_name = "star_router"

    star_container = client.containers.run(
        name=router_name,
        image=ROUTER_IMAGE,
        environment=ENV_VARS,
        privileged=True,
        tty=True,
        detach=True,
        labels={
            "simulation.project": tor_sim_consts.PROJECT_LABEL,
            "simulation.run": tor_sim_consts.RUN_LABEL,
        },
    )

    for _ in range(10):
        if star_container.status == "running":
            break
        time.sleep(1)
        star_container.reload()

    star_container.exec_run("sh -c 'sysctl -w net.ipv4.ip_forward=1'")

    router_log.info(
        f"Star Container Run command executed: container status: {star_container.status}"
    )

    # Connect star router to all networks assigned to each gateway address
    for net_info in nets_to_serve:
        router_log.info(f"Attempting to connect star to {net_info.gateway}")
        net_info.docker_network.connect(
            container=star_container,
            ipv4_address=net_info.gateway,
        )

    star_router = RouterInfo(
        docker_container=star_container,
        name=router_name,
        type="router",
        networks=nets_to_serve,
    )

    return star_router


# Create Router Containers
# kwargs for future expansion with different topologies. For now, only implement star
def create_router_containers(
    docker_client: DockerClient, nets_to_serve: list[NetworkInfo], connect_type="star"
) -> RouterInfo:

    # Sanity Check if client is initialized
    if not docker_client.ping():
        raise RuntimeError(
            "Unable to create router containers: cannot connect to docker engine!"
        )

    match connect_type:
        case "star":
            router_log.info("Creating Star Topology Router")
            container_info = _create_star_container(docker_client, nets_to_serve)
        case _:
            raise ValueError(
                "No other topologies other than star have been implemented at this time"
            )

    router_log.info(f"Router info container {container_info.name} returned")
    return container_info


if __name__ == "__main__":
    router_log.error("router.py is not a standalone script!")
    exit(1)
