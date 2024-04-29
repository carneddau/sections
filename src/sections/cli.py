from os import makedirs
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
        ...,
        "-d",
        "--data",
        exists=True,
        readable=True,
        resolve_path=True,
        dir_okay=False,
        help="DAT file with river section data.",
    ),
    river_names: Path = Option(
        ...,
        "-r",
        "--river-names",
        exists=True,
        readable=True,
        resolve_path=True,
        dir_okay=False,
        help="INI file containing short river name mappings.",
    ),
    output_dir: Path = Option(
        Path(".").resolve(strict=True),
        "-o",
        "--output-dir",
        readable=True,
        writable=True,
        resolve_path=True,
        file_okay=False,
        dir_okay=True,
        show_default=False,
        help="Output directory for csv data. Defaults to current working directory.",
    ),
):
    makedirs(output_dir, exist_ok=True)

    try:
        sections = read_and_process_sections(data)
    except ValueError as err:
        err_console.print(f"Parsing sections in '{data.name}' failed")
        raise Exit(1) from err
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

    write_rivers_to_csv(mapping, rivers, output_dir)


def write_rivers_to_csv(
    mapping: dict[int, str],
    rivers: dict[int, list[Section]],
    output_dir: Path,
):
    for riv_number, river in rivers.items():
        file_path = output_dir / f"{mapping[riv_number]}.csv"
        with uopen(file_path, mode="w") as file:

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
    interface()
