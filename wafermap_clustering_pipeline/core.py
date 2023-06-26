# MODULES
import platform
from pathlib import Path

# CONFIGS
from .configs.config import Config
from .configs.logging import setup_logger


if __name__ == "__main__":
    # LIBS
    from .libs.pipeline_lib import PipeLine

    CONFIGS = Config(
        platform=platform.system().lower(),
        conf_path=Path(__file__).parent / "configs" / "config.json",
    )

    LOGGER = setup_logger(
        name="clustering",
        directory=Path(CONFIGS.directories.logs),
    )

    pipeline = PipeLine(config=CONFIGS, logger=LOGGER)
    pipeline.start()
