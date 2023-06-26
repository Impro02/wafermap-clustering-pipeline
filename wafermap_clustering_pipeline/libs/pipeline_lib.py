# MODULES
import threading
from logging import Logger

# LIBS
from ..libs.process_lib import Process

# CONFIG
from ..configs.config import Config


class PipeLine:
    def __init__(self, config: Config, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.process = Process(config=self.config, logger=self.logger)

    def start(self):
        if self.process.running:
            return self.logger.warning("PipeLine is already running.")

        self.process.running = True
        self.thread = threading.Thread(target=self.process.process_klarfs)
        self.thread.start()
        self.logger.info("PipeLine started.")

    def stop(self):
        if not self.process.running:
            return self.logger.warn("PipeLine is not running.")

        self.process.running = False
        self.thread.join(timeout=5)  # Add a timeout to avoid blocking indefinitely

        self.logger.info("PipeLine stopped.")
