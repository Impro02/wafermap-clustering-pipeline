# MODULES
from dataclasses import dataclass, field
from pathlib import Path

# WAFERMAP-CLUSTERING
from wafermap_clustering.configs.config import (
    KlarfFormat,
    Config as WafermapClusteringConfig,
    DirectoryConfig as ClusteringDirectoryConfig,
)


def check_klarf_formart(format: str):
    if format not in [item.value for item in KlarfFormat]:
        raise ValueError(f"{format=} is not allowed as klarf format")

    return True


@dataclass
class DirectoryConfig(ClusteringDirectoryConfig):
    input: Path
    output: Path
    error: Path


@dataclass
class MailingConfig:
    host: str
    port: int
    sender: str
    receiver: str


@dataclass
class MultiProcessingConfig:
    max_workers: int


class Config(WafermapClusteringConfig):

    klarf_returned: str = field(init=False)
    clustering_algo: str = field(init=False)

    directories: DirectoryConfig = field(init=False)
    multi_processing: MultiProcessingConfig = field(init=False)
    mailing: MailingConfig = field(init=False)

    def __post_init__(self):
        try:
            super().__post_init__()
            self.klarf_returned = self.raw_data.get("klarf_returned")
            self.clustering_algo = self.raw_data.get("clustering_algo")

            directories_config = self.raw_data.get("directories", {})
            multi_processing_config = self.raw_data.get("multi_processing")
            mailing_config = self.raw_data.get("mailing")

            self.directories.input = Path(directories_config.get("input"))
            self.directories.output = Path(directories_config.get("output"))
            self.directories.error = Path(directories_config.get("error"))

            self.multi_processing = MultiProcessingConfig(**multi_processing_config)
            self.mailing = MailingConfig(**mailing_config)

            check_klarf_formart(format=self.klarf_returned)
        except Exception as ex:
            print(f"Configuration file {self.conf_path} is invalid: {ex}")
            exit()
