from pathlib import Path
from datetime import datetime


class ConversionLogger:

    def __init__(self, log_file):

        self.log_file = Path(log_file)

        self.log_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    def write(
        self,
        level,
        message
    ):

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        line = (
            f"[{now}] "
            f"[{level}] "
            f"{message}\n"
        )

        with open(
            self.log_file,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(line)

    def success(self, msg):
        self.write("SUCCESS", msg)

    def error(self, msg):
        self.write("ERROR", msg)

    def skipped(self, msg):
        self.write("SKIPPED", msg)