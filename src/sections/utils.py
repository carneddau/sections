"""Module for simple helper methods with no dependencies within the package"""

from functools import cache, partial
from importlib.metadata import version as _version
from logging import Formatter, getLogger
from sys import maxsize

from rich.console import Console
from rich.logging import RichHandler


@cache
def package() -> str:
    """Get the name of the top-level package"""
    return __name__.split(".")[0]


@cache
def version() -> str:
    """Get the version of the top-level package"""
    return _version(package())


def create_basic_logger(name: str, log_level: str) -> None:
    logger = getLogger(name)

    handler = RichHandler(rich_tracebacks=True)
    handler.setFormatter(Formatter(fmt="%(name)s:%(message)s"))
    logger.addHandler(handler)

    logger.setLevel(log_level)


uopen = partial(open, encoding="UTF-8")
err_console = Console(stderr=True, style="red")
console = Console(stderr=False)
file_console = partial(Console, width=maxsize)
