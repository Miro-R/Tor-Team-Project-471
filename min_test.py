# Minimal Simulator Test
import logging
import subprocess
from tkinter.constants import CURRENT

from docker.client import DockerClient

import tor_sim_consts
from container import ContainerInfo, create_container
from networking import create_docker_networks

# from router_depricated import create_router_containers

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


# Basic test of container orchestration
def test(client: DockerClient):

    debug_logger = logging.getLogger(__name__)

    if not client.ping():
        debug_logger.debug("Docker Ping failed!")
        raise RuntimeError("Cannot connect to docker!")

    debug_logger.info(f"Run label: {tor_sim_consts.RUN_LABEL}")

    # Create three networks
    try:
        networks = create_docker_networks(client, "10.0.0.0/16", 3, 24)

        for net in networks:
            debug_logger.info(f"{net.name}: {net.subnet}, gateway={net.gateway}")

            # create containers in networks (dgaf about types, this is a minimal test)
            curr_container = create_container(network=net, client=client)
            debug_logger.info(f"    Created {curr_container.name}")
        debug_logger.info(f"Created {len(networks)} networks")

        # router = create_router_containers(client, networks)
        # debug_logger.info(f"Created Router: {router.name}")

        print("Test complete (see logger), press any key to cleanup")
        input()

        # since this is a minimal test, I will not repeat myself and just burn it down after completion
        dirty_cleanup(client)

    except Exception as e:
        dirty_cleanup(client)
        raise Exception("Test failed, exception details: " + str(e))


# fail - burn it down
def dirty_cleanup(client: DockerClient):

    # Remove all containers by our project label
    containers = client.containers.list(
        all=True,
        filters={"label": f"simulation.project={tor_sim_consts.PROJECT_LABEL}"},
    )

    for container in containers:
        container.remove(force=True)

    # remove all networks
    networks = client.networks.list(
        filters={"label": f"simulation.project={tor_sim_consts.PROJECT_LABEL}"}
    )
    for network in networks:
        network.remove()
