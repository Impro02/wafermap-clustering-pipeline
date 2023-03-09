# MODULES
from dataclasses import dataclass

# WAFERMAP-CLUSTERING
from wafermap_clustering.models.config import Config as ClusteringConfig


@dataclass
class MailingConfig:
    host: str
    port: int
    sender: str
    receiver: str


@dataclass
class PathConfig:
    input: str
    output: str
    error: str


@dataclass
class Config(ClusteringConfig):
    time_sleep: int
    path: PathConfig
    mailing: MailingConfig
