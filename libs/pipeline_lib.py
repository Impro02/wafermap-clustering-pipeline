# MODULES
import threading
import time
import os
from logging import Logger
import concurrent.futures


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
        self.clustering = Clustering(config=self.config, logger=self.logger)

    @property
    def is_running(self):
        return self.running

    def stop(self):
        self.running = False

        if self.process_thread is not None:
            self.process_thread.join()
            self.logger.info("Pipeline ended...")

    def start(self, callback=None):
        if self.is_running:
            self.logger.warning("Pipeline is already running.")
        else:
            self.logger.info("Pipeline started...")
            self.running = True

            self.process_thread = threading.Thread(
                target=self._process,
                kwargs={
                    "callback": callback,
                    "multi_processing": self.config.multi_processing.use_multi_processing,
                    "max_workers": self.config.multi_processing.max_workers,
                },
            )
            self.process_thread.start()

    def _process(self, callback, multi_processing: bool = False, max_workers=None):
        while self.running:
            klarf_paths, nbr_klarfs = file.get_files(
                path=self.config.path.input, sort_by_modification_date=True
            )

            if nbr_klarfs == 0:
                # Add a sleep here to avoid CPU hogging
                time.sleep(0.1)
                continue

            tic = time.time()

            if multi_processing:
                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=max_workers
                ) as executor:
                    futures = [
                        executor.submit(
                            self._process_klarf, klarf_path, self.config.path.output
                        )
                        for klarf_path in klarf_paths
                    ]

                    for future in concurrent.futures.as_completed(futures):
                        results = future.result()
                        if results and callback is not None:
                            callback(results)
            else:
                for klarf_path in klarf_paths:
                    results = self._process_klarf(
                        klarf_path=klarf_path, output_dir=self.config.path.output
                    )

                    if results and callback is not None:
                        callback(results)

            self.logger.info(f"Batch executed in {time.time() - tic}s")

    def _process_klarf(self, klarf_path, output_dir):
        klarf = os.path.basename(klarf_path)
        klarf_name, klarf_extension = os.path.splitext(klarf)

        try:
            if not file.check_file_size(klarf_path):
                self.logger.warning(f"Timeout exceeded to process {klarf_path=}")
                return None

            output_path = os.path.join(
                output_dir, f"{klarf_name}_clustered{klarf_extension}"
            )

            results = self.clustering.apply(
                klarf_path=klarf_path, output_path=output_path
            )

            if not len(results) == 0 and os.path.exists(klarf_path):
                os.remove(klarf_path)

                return results

            else:
                self.logger.error(msg=f"Unable to remove {klarf=}")

        except Exception as ex:
            if os.path.exists(klarf_path):
                file.move(
                    src=klarf_path, dest=os.path.join(self.config.path.error, klarf)
                )

            message_error = mailing.send_mail_error(
                klarf=klarf,
                error_path=self.config.path.error,
                config=self.config.mailing,
            )

            self.logger.critical(msg=message_error, exc_info=ex)
