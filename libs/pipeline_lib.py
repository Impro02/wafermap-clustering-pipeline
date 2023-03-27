# MODULES
import time
import os
from pathlib import Path
from logging import Logger
import threading

# MODELS
from models.config import Config

# WAFERMAP-CLUSTERING
from wafermap_clustering.wafermap_clustering import Clustering

# UTILS
from utils import mailing, file


class PipeLine:
    def __init__(self, config: Config, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.running = False
        self.thread = None
        self.clustering = Clustering(config=self.config, logger=self.logger)

    @property
    def is_running(self):
        return self.running

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

        self.logger.info("Pipeline ended...")

    def start(self, callback=None):
        if self.is_running:
            self.logger.warning("Pipeline is already running.")
        else:
            self.logger.info("Pipeline started...")
            self.running = True

            self.thread = threading.Thread(target=self._process, args=(callback,))
            self.thread.start()

    def _process(self, callback):
        while self.running:
            klarf_paths, nbr_klarfs = file.get_files(
                path=self.config.path.input, sort_by_modification_date=True
            )

            if not nbr_klarfs == 0:
                for klarf_path in klarf_paths:
                    klarf = os.path.basename(klarf_path)
                    klarf_name, klarf_extension = os.path.splitext(klarf)

                    try:
                        if file.check_file_size(klarf_path):
                            output_path = (
                                Path(self.config.path.output)
                                / f"{klarf_name}_clustered{klarf_extension}"
                            )

                            results = self.clustering.apply(
                                klarf_path=klarf_path,
                                output_path=output_path,
                            )

                            if not len(results) == 0 and os.path.exists(klarf_path):
                                os.remove(klarf_path)

                                if callback is not None:
                                    callback(results)
                            else:
                                self.logger.error(
                                    msg=f"Unable to remove {klarf=}",
                                )

                    except Exception as ex:

                        if os.path.exists(klarf_path):
                            file.move(
                                src=klarf_path,
                                dest=os.path.join(self.config.path.error, klarf),
                            )

                        message_error = mailing.send_mail_error(
                            klarf=klarf,
                            error_path=self.config.path.error,
                            config=self.config.mailing,
                        )

                        self.logger.critical(
                            msg=message_error,
                            exc_info=ex,
                        )

                    # Add a sleep here to avoid CPU hogging
                    time.sleep(0.1)
