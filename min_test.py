import logging
import subprocess

from docker.client import DockerClient

import tor_sim_consts
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

        debug_logger.info(f"Created {len(networks)} networks")

        # router = create_router_containers(client, networks)
        # debug_logger.info(f"Created Router: {router.name}")

        print("Test complete (see logger), press any key to cleanup")
        input()
        for net in networks:
            net.docker_network.remove()
        # router.docker_container.remove(force=True)

    except Exception as e:
        dirty_cleanup()
        raise Exception("Test failed, exception details: " + str(e))


def dirty_cleanup():
    subprocess.run(
        "sh -c 'docker network ls --filter label=simulation.project=tor-network-471 -q | xargs docker network rm'"
    )
    # subprocess.run("docker stop star_router && docker rm star_router")
