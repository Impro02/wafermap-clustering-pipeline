# MODULES
import json
import platform
import os
from pathlib import Path

# MODELS
from models.config import Config, MailingConfig, PathConfig, MultiProcessingConfig

# WAFERMAP-CLUSTERING
from wafermap_clustering.models.config import ClusteringConfig


def load_config(filepath: Path):
    root_config, clustering_config, path_config, mailing_config = {}, {}, {}, {}

    platform_system = platform.system().lower()
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as json_data_file:
            try:
                root_config: dict = json.load(json_data_file)
                clustering_config = root_config.get("clustering", {})
                mailing_config = root_config.get("mailing", {})
                path_config = {}
                multi_processing_config = root_config.get("multi_processing", {})

                platform_config = root_config.get("platforms", [])
                if platform_system in platform_config:
                    path_config: dict = platform_config[platform_system]

            except Exception as ex:
                print(f"Configuration file {filepath} is invalid: {ex}")
                exit()

    return Config(
        time_out=root_config.get("time_out", 5),
        platform=platform_system,
        attribute=root_config.get("attribute", "CLUSTER_ID"),
        path=PathConfig(
            input=path_config.get("input", "/data/clustering/tmp"),
            output=path_config.get("output", "/data/clustering/output"),
            error=path_config.get("error", "/data/clustering/error"),
        ),
        clustering=ClusteringConfig(
            eps=clustering_config.get("eps", 4),
            min_samples=clustering_config.get("min_samples", 3),
        ),
        mailing=MailingConfig(
            host=mailing_config.get("host", None),
            port=mailing_config.get("port", None),
            sender=mailing_config.get("sender", None),
            receiver=mailing_config.get("receiver", None),
        ),
        multi_processing=MultiProcessingConfig(
            use_multi_processing=multi_processing_config.get(
                "use_multi_processing", False
            ),
            max_workers=multi_processing_config.get("max_workers", 3),
            num_files=multi_processing_config.get("num_files", 5),
        ),
    )
