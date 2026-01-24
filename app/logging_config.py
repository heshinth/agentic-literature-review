import logging

from rich.logging import RichHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

console_handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    show_time=True,
    show_level=True,
    show_path=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[console_handler],
)


def get_logger(name: str):
    return logging.getLogger(name)
