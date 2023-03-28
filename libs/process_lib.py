# MODULES
from pathlib import Path
from logging import Logger
import time
import os
import multiprocessing as mp

# MODELS
from models.config import Config

# WAFERMAP-CLUSTERING
from wafermap_clustering.wafermap_clustering import Clustering

# UTILS
from utils import mailing, file


class Process:
    def __init__(self, config: Config, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.running = False
        self.clustering = Clustering(config=self.config, logger=self.logger)

    def process_klarfs(
        self,
    ):
        while self.running:
            klarf_paths, nbr_klarfs = file.get_files(
                path=self.config.path.input, sort_by_modification_date=True
            )

            if nbr_klarfs == 0:
                # Add a sleep here to avoid CPU hogging
                time.sleep(0.1)
                continue

            tic = time.time()

            multi_processing = (
                self.config.multi_processing.use_multi_processing
                and nbr_klarfs > self.config.multi_processing.num_files
            )
            if multi_processing:
                with mp.Pool(
                    processes=self.config.multi_processing.max_workers
                ) as pool:
                    results = pool.starmap(
                        self.process_klarf,
                        [
                            (klarf_path, self.config.path.output)
                            for klarf_path in klarf_paths
                        ],
                    )
                    pool.close()
                    pool.join()

                    [
                        self.logger.info(
                            msg=f"({repr(clustering)}) was processed in {clustering.processing_timestamp} [clusters={clustering.clusters}]"
                        )
                        for clustering_result in results
                        for clustering in clustering_result
                    ]

            else:
                for klarf_path in klarf_paths:
                    results = self.process_klarf(
                        klarf_path=klarf_path, output_dir=self.config.path.output
                    )

            self.logger.info(
                f"Batch of {nbr_klarfs} klarf(s) executed in {time.time() - tic}s [{multi_processing=}]"
            )

    def process_klarf(self, klarf_path: Path, output_dir: Path):
        klarf = os.path.basename(klarf_path)
        klarf_name, klarf_extension = os.path.splitext(klarf)

        output_path = os.path.join(
            output_dir, f"{klarf_name}_clustered{klarf_extension}"
        )

        try:
            if file.check_file_size(klarf_path, timeout=self.config.time_out):
                results = self.clustering.apply(
                    klarf_path=klarf_path, output_path=output_path
                )

                if len(results) == 0 or not os.path.exists(klarf_path):
                    return self.logger.error(msg=f"Unable to remove {klarf=}")

                os.remove(klarf_path)

                return results

        except TimeoutError as ex:
            self.logger.warning(
                msg=f"Timeout exceeded while cheking size of {klarf_path=}",
                exc_info=ex,
            )
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
