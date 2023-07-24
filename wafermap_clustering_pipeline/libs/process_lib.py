# MODULES
import os
from pathlib import Path

# WAFERMAP-CLUSTERING
from wafermap_clustering.wafermap_clustering import Clustering

# KLARF_READER
from klarf_reader.klarf import Klarf

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
            file.check_file_size(
                klarf_path,
                timeout=self.config.time_out,
            )

            content = Klarf.load_from_file_with_raw_content(filepath=klarf_path)

            results = self.clustering.apply_from_content(
                content=content,
                output_directory=Path(
                    self.config.directories.output.format(
                        **{"loader_name": content[0].inspection_station_id.id}
                    )
                ),
                original_klarf_name=klarf_path.stem,
                original_klarf_extension=klarf_path.suffix,
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

        except (TimeoutError, Exception) as ex:
            if os.path.exists(klarf_path):
                file.move(src=klarf_path, dest=self.config.directories.error / klarf)

            message_error = mailing.send_mail_error(
                klarf=klarf,
                error_path=self.config.directories.error,
                config=self.config.mailing,
            )

            if isinstance(ex, TimeoutError):
                logger.warning(
                    msg=f"Timeout exceeded while cheking size of {klarf_path=}",
                    exc_info=ex,
                )
            else:
                logger.critical(msg=message_error, exc_info=ex)
