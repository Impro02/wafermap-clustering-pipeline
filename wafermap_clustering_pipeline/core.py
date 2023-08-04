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
from .utils import file

# CONFIGS
from .configs.config import Config
from .configs.logging import setup_logger


def process_lot_end_file(
    file_path: Path,
    output_path: str,
    logger: Logger,
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

    file.move(
        src=file_path,
        dest=Path(output_path) / file_path.name,
    )

    logger.info(f"{file_path.name=} was successfully moved to {output_path}.")

    return True


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

    def process_file(self, file_path: Path):
        lot_end_moved = process_lot_end_file(
            file_path=Path(file_path),
            output_path=self._config.directories.output,
            logger=self._logger,
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
