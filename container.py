# Creates Client and Server containers, holds base container
from dataclasses import dataclass

from docker.models.containers import Container

if __name__ == "__main__":
    print("container.py is not a standalone script!")
    exit(1)


@dataclass
class BaseContainerInfo:
    docker_container: Container
    name: str
    type: str
