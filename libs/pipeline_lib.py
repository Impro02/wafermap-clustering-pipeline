# MODULES
import time
import os
from pathlib import Path
from logging import Logger

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
        self.clustering = Clustering(config=self.config, logger=self.logger)

    def start(self):
        while True:
            time.sleep(self.config.time_sleep)

            klarf_paths, nbr_klarfs = file.get_files(
                path=self.config.path.input, sort_by_modification_date=True
            )

            if not nbr_klarfs == 0:
                for klarf_path in klarf_paths:
                    klarf = os.path.basename(klarf_path)
                    klarf_name, klarf_extension = os.path.splitext(klarf)

                    try:
                        if file.check_file_size(klarf_path):
                            output_path = (
                                Path(self.config.path.output)
                                / f"{klarf_name}_clustered{klarf_extension}"
                            )

                            results = self.clustering.apply(
                                klarf_path=klarf_path,
                                output_path=output_path,
                            )

                            if not len(results) == 0 and os.path.exists(klarf_path):
                                os.remove(klarf_path)
                            else:
                                self.logger.error(
                                    msg=f"Unable to remove {klarf=}",
                                )

                    except Exception as ex:
                        file.move(
                            src=klarf_path,
                            dst=os.path.join(self.config.path.error, klarf),
                        )

                        message_error = mailing.send_mail_error(
                            klarf=klarf,
                            error_path=self.config.path.error,
                            config=self.config.mailing,
                        )

                        self.logger.critical(
                            msg=message_error,
                            exc_info=ex,
                        )
