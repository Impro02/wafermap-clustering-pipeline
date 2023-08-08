# MODULES
import platform
import time
import os
from multiprocessing import Pool
from pathlib import Path
from logging import Logger

# LIBS
from wafermap_clustering_pipeline.libs.process_lib import Process

# UTILS
from .utils import file, mailing

# CONFIGS
from .configs.config import Config
from .configs.logging import setup_logger


class Processor:
    def __init__(
        self,
        config: Config,
        logger: Logger,
    ) -> None:
        self._config = config
        self._logger = logger
        # Create the process instance
        self.process = Process(
            config=self._config,
        )

    def _process_lot_end_file(
        self,
        file_path: Path,
        output_path: str,
    ):
        if not file_path.exists() or not file_path.suffix == ".trf":
            return False

        with open(file_path, "r") as f:
            raw_content = f.readlines()

        for line in raw_content:
            if line.lstrip().lower().startswith("inspectionstationid"):
                inspection_station_id = line.split(";")[0].split(" ")
                inspection_station_id = [id.strip('"') for id in inspection_station_id]
                inspection_station_id = inspection_station_id[1:4]

                output_path = output_path.format(
                    **{"loader_name": inspection_station_id[-1]}
                )

        try:
            dest = Path(output_path) / file_path.name

            file.move(
                src=file_path,
                dest=dest,
            )

            self._logger.info(
                f"{file_path.name=} was successfully moved to {output_path}."
            )
        except Exception as ex:
            if file_path.exists():
                file.move(
                    src=file_path,
                    dest=Path(self._config.directories.error) / file_path.name,
                )

            message_error = mailing.send_mail_error(
                file=file_path,
                error_path=self._config.directories.error,
                config=self._config.mailing,
            )

            self._logger.critical(msg=message_error, exc_info=ex)

        return True

    def process_file(self, file_path: Path):
        file.copy(
            file_path,
            Path(self._config.directories.archive) / file_path.name,
        )

        lot_end_moved = self._process_lot_end_file(
            file_path=Path(file_path),
            output_path=self._config.directories.output,
        )

        if not lot_end_moved:
            self.process.process_klarf(klarf_path=file_path)


if __name__ == "__main__":
    CONFIGS = Config(
        platform=platform.system().lower(),
        conf_path=Path(__file__).parent / "configs" / "config.json",
    )

    LOGGER = setup_logger(
        name="clustering",
        directory=Path(CONFIGS.directories.logs),
    )

    # Create a process pool to manage the worker processes
    pool = Pool(
        processes=CONFIGS.multi_processing.max_workers,
        maxtasksperchild=CONFIGS.multi_processing.max_tasks_per_child,
    )

    LOGGER.info(
        f"Creation of process pool (max_workers={CONFIGS.multi_processing.max_workers})."
    )

    processor = Processor(
        config=CONFIGS,
        logger=LOGGER,
    )

    try:
        while True:

            files = [
                os.path.join(CONFIGS.directories.input, f)
                for f in os.listdir(CONFIGS.directories.input)
                if os.path.isfile(os.path.join(CONFIGS.directories.input, f))
            ]

            if (num_files := len(files)) == 0:
                LOGGER.info(f"Batch ended with no file processed.")
            else:
                results = [
                    pool.apply_async(processor.process_file, args=(Path(file_path),))
                    for file_path in files
                ]

                for result in results:
                    result.get()

                LOGGER.info(f"Batch ended with {num_files} file(s) processed.")

            time.sleep(CONFIGS.interval)

    except KeyboardInterrupt:
        LOGGER.info(f"File watcher stopped because interruped by user.")

        pool.close()
        pool.join()
