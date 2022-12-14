from csv import reader
from os import PathLike
from typing import Optional

from .schema import Section, SectionRaw
from .utils import uopen


def read_sections(file_name: PathLike) -> list[list[str]]:
    sections: list[list[str]] = []
    with uopen(file_name) as file:
        # Remove empty lines
        lines = [line.strip() for line in file.readlines()]
        lines = [line for line in lines if line != ""]

        cross_sections: list[str] = []

        for index, line in enumerate(lines, start=1):
            cross_sections.append(line)

            # Append the section when if we are at the last line of either the file or the section
            if index == len(lines) or lines[index].startswith("NEWSEC"):
                sections.append(cross_sections.copy())
                cross_sections.clear()

    return sections


def _string_or_none(input: str) -> Optional[str]:
    return input.strip() if input != "" else None


def process_raw_sections(sections: list[list[str]]) -> list[SectionRaw]:
    """Strip whitespace"""
    processed_sections: list[SectionRaw] = []

    for section_in in sections:

        cross_sections: list[list[str]] = []
        metadata: dict[str, list[Optional[str]]] = {}
        for row in reader(section_in):

            len_row = len(row)

            if len_row != 6:
                raise ValueError(f"Expected 6 elements for each row, got {len_row}")

            row_nones = [_string_or_none(x) for x in row]

            identifier = row_nones[0]

            if identifier is None:
                raise ValueError("first element of a record was empty")

            if identifier in ["XSS", "XSN"]:
                if any([x is None for x in row_nones]):
                    raise ValueError(
                        f"an element in a cross section was None: {row_nones}"
                    )
                cross_sections.append(row_nones[1:])  # type: ignore
            else:
                if identifier in [
                    "NEWSEC",
                    "SECDATE",
                    "BEDMATERIAL",
                    "SECBEARING",
                    "SECCOORDS",
                ]:
                    if metadata.get(identifier) is not None:
                        raise ValueError(f"metadata key already exists {identifier}")
                    metadata[identifier] = row_nones[1:]

        section = SectionRaw(metadata, cross_sections)
        processed_sections.append(section)

    return processed_sections


def process_sections(sections_raw: list[SectionRaw]) -> list[Section]:
    sections: list[Section] = []

    for section_raw in sections_raw:
        sections.append(Section.from_raw(section_raw))

    return sections


def read_short_rivername_mapping(file_name: PathLike) -> dict[int, str]:
    mapping: dict[int, str] = {}

    with uopen(file_name) as file:

        # Remove empty lines
        lines = [
            line.strip()
            for line in file.readlines()
            if line.strip().startswith("SHORT_RIVERNAME")
        ]

        for line in lines:
            split_line = line.split(sep="=")
            try:
                number = int(split_line[0][-1])
            except ValueError as err:
                raise ValueError(
                    f"Could not parse integer from short river name {line}"
                ) from err

            name = split_line[1]
            mapping[number] = name

    return mapping


def read_and_process_sections(data: PathLike) -> list[Section]:
    sections = read_sections(data)
    raw_sections = process_raw_sections(sections)
    return process_sections(raw_sections)


def generate_rivers(sections: list[Section]):
    rivers: dict[int, list[Section]] = {}

    for section in sections:
        riv_number = section.river_num

        if rivers.get(riv_number) is None:
            rivers[riv_number] = []

        rivers[riv_number].append(section)
    return rivers
