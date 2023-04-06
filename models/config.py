# MODULES
from dataclasses import dataclass
from pathlib import Path

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
    input: Path
    output: Path
    error: Path


@dataclass
class MultiProcessingConfig:
    use_multi_processing: bool
    max_workers: int
    num_files: int


@dataclass
class LoggingConfig:
    path: Path


@dataclass
class Config(ClusteringConfig):
    time_out: int
    cpu_hog_tempo: float
    klarf_returned: str
    path: PathConfig
    mailing: MailingConfig
    multi_processing: MultiProcessingConfig
    logging: LoggingConfig
    clustering_algo: str
