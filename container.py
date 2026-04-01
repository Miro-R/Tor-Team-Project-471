# Creates Client and Server containers, holds base container
from dataclasses import dataclass

from docker.client import DockerClient
from docker.errors import NotFound
from docker.models.containers import Container

import tor_sim_consts
from networking import NetworkInfo

if __name__ == "__main__":
    print("container.py is not a standalone script!")
    exit(1)


@dataclass
class ContainerInfo:
    docker_container: Container
    name: str
    image: str


# Creates a client - typically on the first network
def create_container(
    network: NetworkInfo,
    client: DockerClient,
    name: str = "",
    image: str = "alpine",
    shell: str = "sh -c",
    command: str = "sleep infinity",
) -> ContainerInfo:

    # check if docker engine is running
    if not client.ping():
        raise RuntimeError("Unable to connect to docker engine!")

    # generate name if blank
    if name == "":
        name = f"{network.name}-{image}"

    # Duplicate name handling
    # Check if name exists and if its been numbered,
    # if not, add right digit to distinguish
    # if so, increment right digit and check again until
    # unique name is found
    container_found = True
    while container_found:
        try:
            client.containers.get(name)
        except NotFound:
            container_found = False
        else:
            parts = name.rsplit("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                base_name, num = parts
                name = f"{base_name}-{int(num) + 1}"  # Name exists with numeric suffix, increment
            else:  # Name exists without numeric suffix, append 0
                name = f"{name}-0"

    # Create container and attach to specified network
    return ContainerInfo(
        docker_container=client.containers.run(
            image=image,
            network=network.name,
            name=name,
            labels={
                "simulation.project": tor_sim_consts.PROJECT_LABEL,
                "simulation.run": tor_sim_consts.RUN_LABEL,
            },
            command=f'{shell} "{command}"',
            detach=True,
        ),
        name=name,
        image=image,
    )
