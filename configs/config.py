# MODULES
import json
import platform
import os
from pathlib import Path
from enum import Enum

# MODELS
from models.config import (
    Config,
    LoggingConfig,
    MailingConfig,
    PathConfig,
    MultiProcessingConfig,
)

# WAFERMAP-CLUSTERING
from wafermap_clustering.models.config import (
    ClusteringConfig,
    DBSCANConfig,
    HDBSCANConfig,
)

from wafermap_clustering.configs.config import KlarfFormat


def check_klarf_formart(format: str):
    if format not in [item.value for item in KlarfFormat]:
        raise ValueError(f"{format=} is not allowed as klarf format")

    return True


def load_config(filepath: Path):
    (
        root_config,
        clustering_config,
        path_config,
        mailing_config,
    ) = ({}, {}, {}, {})

    platform_system = platform.system().lower()
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as json_data_file:
            try:
                root_config: dict = json.load(json_data_file)

                klarf_format_config = root_config.get("klarf_returned", "")
                check_klarf_formart(format=klarf_format_config)

                clustering_config = root_config.get("clustering", {})
                mailing_config = root_config.get("mailing", {})
                path_config = {}
                multi_processing_config = root_config.get("multi_processing", {})
                logging_config = root_config.get("logging", {})

                platform_config = root_config.get("platforms", [])
                if platform_system in platform_config:
                    path_config: dict = platform_config[platform_system]

            except Exception as ex:
                print(f"Configuration file {filepath} is invalid: {ex}")
                exit()

    return Config(
        time_out=root_config.get("time_out", 5),
        cpu_hog_tempo=root_config.get("cpu_hog_tempo", 0.1),
        klarf_returned=klarf_format_config,
        platform=platform_system,
        attribute=root_config.get("attribute", "CLUSTER_ID"),
        path=PathConfig(
            input=Path(path_config.get("input")),
            output=Path(path_config.get("output")),
            error=Path(path_config.get("error")),
        ),
        clustering_algo=root_config.get("clustering_algo", "dbscan"),
        clustering=ClusteringConfig(
            dbscan=DBSCANConfig(**clustering_config.get("dbscan")),
            hdbscan=HDBSCANConfig(**clustering_config.get("hdbscan")),
        ),
        mailing=MailingConfig(**mailing_config),
        multi_processing=MultiProcessingConfig(**multi_processing_config),
        logging=LoggingConfig(path=Path(logging_config.get("path", os.getcwd()))),
    )
