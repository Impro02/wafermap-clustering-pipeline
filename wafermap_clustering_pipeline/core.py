# MODULES
import platform
import time
import os
from multiprocessing import Pool
from pathlib import Path
from logging import Logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from wafermap_clustering_pipeline.libs.process_lib import Process

# CONFIGS
from .configs.config import Config
from .configs.logging import setup_logger


class FileHandler(FileSystemEventHandler):
    def __init__(
        self,
        pool,
        process: Process,
        logger: Logger,
    ):
        super().__init__()
        self._pool = pool
        self._process = process
        self._logger = logger

    def on_created(self, event):
        # Check if the event is for a file
        if event.is_directory:
            return

        self._logger.info(f"New file {(file_path := event.src_path)} detected")

        # Trigger a task to process the new file
        self._pool.apply_async(self._process.process_klarf, args=(Path(file_path),))


if __name__ == "__main__":
    CONFIGS = Config(
        platform=platform.system().lower(),
        conf_path=Path(__file__).parent / "configs" / "config.json",
    )

    LOGGER = setup_logger(
        name="clustering",
        directory=Path(CONFIGS.directories.logs),
    )

    LOGGER.info(
        f"Creation of process pool (max_workers={CONFIGS.multi_processing.max_workers})"
    )

    # Create a process pool to manage the worker processes
    pool = Pool(processes=CONFIGS.multi_processing.max_workers)

    # Create the process instance
    process = Process(config=CONFIGS)

    LOGGER.info(
        f"Creation of a file watcher to monitor new files from {CONFIGS.directories.input})"
    )

    # Create a file watcher to monitor the folder for new files
    event_handler = FileHandler(pool, process, LOGGER)
    observer = Observer()
    observer.schedule(event_handler, path=CONFIGS.directories.input, recursive=False)
    observer.start()

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
            pool.apply_async(process.process_klarf, args=(Path(file_path),))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
