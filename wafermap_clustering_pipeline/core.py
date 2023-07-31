# MODULES
import platform
import time
import os
from pathlib import Path
from logging import Logger
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

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

    logger.info(f"{file_path.name=} was successfully moved to {output_path}")

    return True


class FileHandler(FileSystemEventHandler):
    def __init__(
        self,
        process: Process,
        logger: Logger,
    ):
        super().__init__()
        self._process = process
        self._logger = logger

    def on_created(self, event):
        self._logger.info(f"New file {(file_path := event.src_path)} detected")

        # Check if the event is for a file
        if event.is_directory:
            return

        lot_end_moved = process_lot_end_file(
            file_path=Path(file_path),
            output_path=self._process.config.directories.output,
            logger=self._logger,
        )

        if not lot_end_moved:
            # Trigger a task to process the new file
            self._process.process_klarf(Path(file_path))


if __name__ == "__main__":
    CONFIGS = Config(
        platform=platform.system().lower(),
        conf_path=Path(__file__).parent / "configs" / "config.json",
    )

    LOGGER = setup_logger(
        name="clustering",
        directory=Path(CONFIGS.directories.logs),
    )

    # Create the process instance
    process = Process(config=CONFIGS)

    LOGGER.info(
        f"Creation of a file watcher to monitor new files from {CONFIGS.directories.input})"
    )

    # Create a file watcher to monitor the folder for new files
    event_handler = FileHandler(process, LOGGER)
    observer = PollingObserver()
    observer.schedule(
        event_handler,
        path=CONFIGS.directories.input,
        recursive=False,
    )
    observer.start()
    observer.is_alive()

    files = [
        os.path.join(CONFIGS.directories.input, f)
        for f in os.listdir(CONFIGS.directories.input)
        if os.path.isfile(os.path.join(CONFIGS.directories.input, f))
    ]

    if (num_files := len(files)) > 0:
        LOGGER.info(
            f"Start the process of {num_files} file already in {CONFIGS.directories.input})"
        )

        # Submit a task to process each file
        for file_path in files:
            lot_end_moved = process_lot_end_file(
                file_path=Path(file_path),
                output_path=CONFIGS.directories.output,
                logger=LOGGER,
            )

            if not lot_end_moved:
                process.process_klarf(Path(file_path))

    stopped = False
    try:
        while True:
            if not os.path.isdir(CONFIGS.directories.input):
                if not stopped:
                    observer.stop()
                    stopped = True

                    LOGGER.info(
                        f"File watcher stoped because target folder missing {CONFIGS.directories.input})"
                    )
            else:
                if stopped:
                    observer = PollingObserver()
                    stopped = False
                    observer.schedule(
                        event_handler,
                        path=CONFIGS.directories.input,
                        recursive=False,
                    )
                    observer.start()

                    LOGGER.info(
                        f"File watcher restart to monitor new files from {CONFIGS.directories.input})"
                    )
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
