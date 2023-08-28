# MODULES
import platform
import time
import os
import multiprocessing
from pathlib import Path
from typing import List

# LIBS
from wafermap_clustering_pipeline.libs.process_lib import Process

# UTILS
from .utils import file

# CONFIGS
from .configs.config import Config
from .configs.logging import setup_logger


def file_processor(
    process: Process,
    input_queue: multiprocessing.JoinableQueue,
):
    logger = setup_logger(
        name="file_processor",
        directory=Path(CONFIGS.directories.logs),
    )

    while True:
        input_file_path: Path = input_queue.get()
        if input_file_path is None:
            break

        logger.info(f"{input_file_path} is processing...")

        process.process_klarf(Path(input_file_path))

        logger.info(f"{input_file_path} process ended...")

        input_queue.task_done()


if __name__ == "__main__":
    CONFIGS = Config(
        platform=platform.system().lower(),
        conf_path=Path(__file__).parent / "configs" / "config.json",
    )

    LOGGER = setup_logger(
        name="clustering",
        directory=Path(CONFIGS.directories.logs),
    )

    # CREATE DIRECTORIES
    os.makedirs(CONFIGS.directories.archive, exist_ok=True)
    os.makedirs(CONFIGS.directories.input, exist_ok=True)
    os.makedirs(CONFIGS.directories.tmp, exist_ok=True)
    os.makedirs(CONFIGS.directories.error, exist_ok=True)
    os.makedirs(CONFIGS.directories.logs, exist_ok=True)

    process = Process(config=CONFIGS)

    input_queue = multiprocessing.JoinableQueue()

    LOGGER.info(
        f"Creation of process pool (max_workers={CONFIGS.multi_processing.max_workers})."
    )
    processes: List[multiprocessing.Process] = []
    for _ in range(CONFIGS.multi_processing.max_workers):
        p = multiprocessing.Process(
            target=file_processor,
            args=(process, input_queue),
        )
        p.start()
        processes.append(p)

    try:
        while True:
            new_files = [
                f for f in Path(CONFIGS.directories.input).iterdir() if f.is_file()
            ]

            LOGGER.info(f"{len(new_files)} file(s) to process...")
            for new_file in new_files:
                try:
                    file.check_file_size(
                        new_file,
                        timeout=CONFIGS.time_out,
                    )
                    new_file = file.move(new_file, CONFIGS.directories.tmp)
                    input_queue.put(Path(new_file))
                except TimeoutError as ex:
                    LOGGER.warning(
                        msg=f"Timeout exceeded while cheking size of {new_file}",
                        exc_info=ex,
                    )

            time.sleep(CONFIGS.interval)

    except KeyboardInterrupt:
        LOGGER.info(f"File watcher stopped because interruped by user.")

        for _ in range(CONFIGS.multi_processing.max_workers):
            input_queue.put(None)

        input_queue.join()

        for p in processes:
            p.join()
