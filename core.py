# MODULES
from pathlib import Path

# CONFIGS
from configs.config import load_config
from configs.logging import setup_logger


CONFIGS_CLUSTERING_PATH = Path("configs") / "config.json"
CONFIGS = load_config(filepath=CONFIGS_CLUSTERING_PATH)

LOGGER = setup_logger(name="clustering", path=CONFIGS.logging.path)

if __name__ == "__main__":
    # LIBS
    from libs.pipeline_lib import PipeLine

    pipeline = PipeLine(config=CONFIGS, logger=LOGGER)
    pipeline.start()
