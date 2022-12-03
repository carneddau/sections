from pathlib import Path

from typer import Option, Typer

from .input import (
    generate_rivers,
    read_and_process_sections,
    read_short_rivername_mapping,
)
from .schema import Section
from .utils import console, uopen

# Allow invocation without subcommand so --version option does not produce an error
interface = Typer()


@interface.command()
def main(
    data: Path = Option(default=..., readable=True),
    river_names: Path = Option(default=..., readable=True),
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


def cli():
    """Run the CLI tool"""
    interface()
