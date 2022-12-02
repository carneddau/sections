from .cli import cli
from .settings import get_settings
from .utils import create_basic_logger, package


def main():
    """
    Set the log level for the top-level package. This log level will propogate to all child modules.

    Using this method avoids creating the root logger, which will cause third party libs
    to spam the log output.
    """
    create_basic_logger(package(), get_settings().log_level)

    cli()


if __name__ == "__main__":
    main()
