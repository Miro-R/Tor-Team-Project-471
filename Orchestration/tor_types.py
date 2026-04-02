from dataclasses import dataclass

from docker.models.containers import Container
from docker.models.networks import Network


@dataclass
class NetworkInfo:
    docker_network: Network
    name: str
    subnet: str
    gateway: str


@dataclass
class ContainerInfo:
    docker_container: Container
    name: str
    image: str
