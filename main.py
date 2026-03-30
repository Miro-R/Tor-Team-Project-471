# Entry point for docker orchestration

import json
import logging
import os
from pathlib import Path

import docker

from networking import NetworkInfo, create_docker_networks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# TODO: Note this in requirements
# Get docker context (works on UNIX machines with default configuration)
def get_docker_context() -> str:

    # setup logging
    logger = logging.getLogger(__name__)

    # Generic DOCKER_HOST env variable
    if os.environ.get("DOCKER_HOST"):
        logger.debug("Using DOCKER_HOST environment variable")
        return os.environ["DOCKER_HOST"]

    config_path = Path.home() / ".docker" / "config.json"
    contexts_dir = Path.home() / ".docker" / "contexts" / "meta"

    # TODO: get rid of this disgusting nesting of conditionals and loops (extract into functions)

    current_context = "default"
    if config_path.exists() and contexts_dir.exists():
        logger.debug(f"Reading Docker config from {config_path}")
        with open(config_path) as config_json:
            config = json.load(config_json)
        current_context = config.get("currentContext", "default")
        logger.debug(f"Current context: {current_context}")

        # iterate through directories to find the current context
        for context_subdir in contexts_dir.iterdir():
            meta_file = context_subdir / "meta.json"

            if meta_file.exists():
                with open(meta_file) as meta_json:
                    meta = json.load(meta_json)

                if meta.get("Name") == current_context:
                    endpoints = meta.get("Endpoints", {})
                    docker_endpoint = endpoints.get("docker", {})
                    host = docker_endpoint.get("Host", "")
                    logger.debug(f"Found context: {current_context} with host: {host}")
                    return host

    # Fallback if all else fails
    default_socket = Path("/var/run/docker.sock")
    if default_socket.exists():
        logger.debug(f"Using fallback default: {default_socket}")
        return f"unix://{default_socket}"

    logger.error("Unable to find docker socket!")
    raise RuntimeError("Could not find docker socket! (Is Docker Engine runnning?)")


def main():

    logger = logging.getLogger(__name__)

    print("Initializing Docker")

    # Open connection to docker engine from environment
    try:
        client = docker.DockerClient(base_url=get_docker_context())
        # client = docker.from_env()
    except Exception as e:
        print(f"Exception details: {e}")
        exit(-1)

    if not client.ping():
        logger.error(
            "There was a problem communicating with Docker Engine. Please check your configuration!"
        )
        client.close()
        exit(1)

    logger.info("Connection with docker established")

    # Close connection to docker engine
    client.close()


if __name__ == "__main__":
    main()
