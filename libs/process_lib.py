# MODULES
import math
import time
import os
import multiprocessing as mp
from typing import Tuple
from pathlib import Path
from logging import Logger

# MODELS
from models.config import Config

# WAFERMAP-CLUSTERING
from wafermap_clustering.wafermap_clustering import Clustering

from configs.logging import setup_logger

# UTILS
from utils import mailing, file


class Process:
    def __init__(self, config: Config, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.running = False
        self.clustering = Clustering(config=self.config)

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
                max_workers = min(
                    mp.cpu_count(), self.config.multi_processing.max_workers
                )
                with mp.Pool(processes=max_workers) as pool:
                    chunksize = max(
                        1,
                        int(math.ceil(len(klarf_paths) / max_workers)),
                    )
                    chunks = [
                        (klarf_paths[i : i + chunksize])
                        for i in range(0, len(klarf_paths), chunksize)
                    ]
                    results = pool.starmap(
                        self.process_chunks,
                        iterable=[(chunk, self.config.path.output) for chunk in chunks],
                    )
                    results = [item for sublist in results for item in sublist]
            else:
                for klarf_path in klarf_paths:
                    results = self.process_klarf(
                        klarf_path=klarf_path, output_dir=self.config.path.output
                    )

            self.logger.info(
                f"Batch of {nbr_klarfs} klarf(s) executed in {time.time() - tic}s [{multi_processing=}]"
            )

    def process_chunks(self, chunk: Tuple[Path], output_dir: str):
        return [
            self.process_klarf(klarf_path=item, output_dir=output_dir) for item in chunk
        ]

    def process_klarf(self, klarf_path: Path, output_dir: Path):
        # get the current process
        process_id = os.getpid()
        logger = setup_logger(name="process_klarf", path=self.config.logging.path)

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

                [
                    logger.info(
                        msg=f"{process_id=} ({repr(clustering)}) was processed in {clustering.processing_timestamp} [clusters={clustering.clusters}]"
                    )
                    for clustering in results
                ]

                if len(results) == 0 or not os.path.exists(klarf_path):
                    return logger.error(msg=f"Unable to remove {klarf=}")

                os.remove(klarf_path)

                return results

        except TimeoutError as ex:
            logger.warning(
                msg=f"Timeout exceeded while cheking size of {klarf_path=}",
                exc_info=ex,
            )
        except Exception as ex:
            if os.path.exists(klarf_path):
                file.move(src=klarf_path, dest=self.config.path.error / klarf)

            message_error = mailing.send_mail_error(
                klarf=klarf,
                error_path=self.config.path.error,
                config=self.config.mailing,
            )

            logger.critical(msg=message_error, exc_info=ex)
