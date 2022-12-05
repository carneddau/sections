from pathlib import Path

from typer import Exit, Option, Typer

from .input import (
    generate_rivers,
    read_and_process_sections,
    read_short_rivername_mapping,
)
from .schema import Section
from .settings import get_settings
from .utils import console, create_basic_logger, err_console, package, uopen

# Allow invocation without subcommand so --version option does not produce an error
interface = Typer()


@interface.command()
def _main(
    data: Path = Option(
        default=...,
        exists=True,
        readable=True,
        resolve_path=True,
        dir_okay=False,
    ),
    river_names: Path = Option(
        default=...,
        exists=True,
        readable=True,
        resolve_path=True,
        dir_okay=False,
    ),
):
    sections = read_and_process_sections(data)
    mapping = read_short_rivername_mapping(river_names)
    rivers = generate_rivers(sections)

    console.print_json(
        data=dict(
            map(
                lambda x: (f"{mapping[x[0]]}", f"{len(x[1])} sections"),
                rivers.items(),
            )
        )
    )

    write_rivers_to_csv(mapping, rivers)


def write_rivers_to_csv(mapping: dict[int, str], rivers: dict[int, list[Section]]):
    for riv_number, river in rivers.items():
        with uopen(f"{mapping[riv_number]}.csv", mode="w") as file:

            file.write(
                "REF,SECTION NUMBER,NAME,DATE,CHAINAGE,OFFSET/BRG,LEVEL,EASTING,NORTHING,BANK,MANNINGS,GROUND,VEGETATION\n"
            )

            for section in river:
                for record in section.csv_records(mapping):
                    file.write(f"{record}\n")


def main():
    """
    Set the log level for the top-level package. This log level will propogate to all child modules.

    Using this method avoids creating the root logger, which will cause third party libs
    to spam the log output.
    """
    create_basic_logger(package(), get_settings().log_level)
    try:
        interface()
    except Exception as err:
        err_console.print(err)
        Exit(1)
