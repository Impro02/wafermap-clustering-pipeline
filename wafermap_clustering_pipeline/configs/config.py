# MODULES
from dataclasses import dataclass, field

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
class MultiProcessingConfig:
    max_workers: int
    max_tasks_per_child: int


@dataclass
class DirectoryConfig(ClusteringDirectoryConfig):
    input: str
    output: str
    error: str


@dataclass
class MailingConfig:
    host: str
    port: int
    sender: str
    receiver: str


class Config(WafermapClusteringConfig):
    time_out: int = field(init=False)
    klarf_returned: str = field(init=False)
    clustering_algo: str = field(init=False)

    directories: DirectoryConfig = field(init=False)
    multi_processing: MultiProcessingConfig = field(init=False)
    mailing: MailingConfig = field(init=False)

    interval: int = field(init=False)

    def __post_init__(self):
        try:
            super().__post_init__()
            self.time_out = self.raw_data.get("time_out")
            self.klarf_returned = self.raw_data.get("klarf_returned")
            self.clustering_algo = self.raw_data.get("clustering_algo")

            directories_config = self.raw_data.get("directories", {})
            multi_processing_config = self.raw_data.get("multi_processing")
            mailing_config = self.raw_data.get("mailing")

            self.directories.input = directories_config.get("input")
            self.directories.output = directories_config.get("output")
            self.directories.error = directories_config.get("error")
            self.multi_processing = MultiProcessingConfig(**multi_processing_config)
            self.mailing = MailingConfig(**mailing_config)

            self.interval = self.raw_data.get("interval")

            check_klarf_formart(format=self.klarf_returned)
        except Exception as ex:
            print(f"Configuration file {self.conf_path} is invalid: {ex}")
            exit()
