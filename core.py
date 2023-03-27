# MODULES
from pathlib import Path

# WAFERMAP-CLUSTERING
from wafermap_clustering.configs.logging_config import setup_logger

# CONFIGS
from configs.config import load_config


CONFIGS_CLUSTERING_PATH = Path("configs") / "config.json"
CONFIGS = load_config(filepath=CONFIGS_CLUSTERING_PATH)

LOGGER = setup_logger(CONFIGS.platform)

if __name__ == "__main__":
    # LIBS
    from libs.pipeline_lib import PipeLine

    pipeline = PipeLine(config=CONFIGS, logger=LOGGER)
    pipeline.start()
