# MODULES
import os
from pathlib import Path

# WAFERMAP-CLUSTERING
from wafermap_clustering.wafermap_clustering import Clustering


# CONNFIG
from ..configs.config import Config
from ..configs.logging import setup_logger

# UTILS
from ..utils import mailing, file


class Process:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.clustering = Clustering(config=self.config)

    def process_klarf(
        self,
        klarf_path: Path,
        logger_name: str = "process_klarf",
    ):
        # get the current process
        process_id = os.getpid()
        logger = setup_logger(
            name=logger_name,
            directory=Path(self.config.directories.logs),
        )

        klarf = os.path.basename(klarf_path)

        try:
            results = self.clustering.apply(
                klarf_path=klarf_path,
                output_directory=self.config.directories.output,
                klarf_format=self.config.klarf_returned,
                clustering_mode=self.config.clustering_algo,
            )

            [
                logger.info(
                    msg=f"{process_id=} processed ({repr(clustering)}) with {self.config.clustering_algo} in {clustering.performance.clustering_timestamp}s [defects={len(clustering.clustered_defects)}, clusters={clustering.clusters}] [klarf ({self.config.klarf_returned}) generated in {clustering.performance.output_timestamp}s]"
                )
                for clustering in results
            ]

            if len(results) == 0 or not os.path.exists(klarf_path):
                return logger.error(msg=f"Unable to remove {klarf=}")

            os.remove(klarf_path)

            return results

        except Exception as ex:
            if os.path.exists(klarf_path):
                file.move(src=klarf_path, dest=self.config.directories.error / klarf)

            message_error = mailing.send_mail_error(
                klarf=klarf,
                error_path=self.config.directories.error,
                config=self.config.mailing,
            )

            logger.critical(msg=message_error, exc_info=ex)
