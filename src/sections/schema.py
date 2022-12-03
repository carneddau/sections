from dataclasses import dataclass
from typing import Optional, Tuple

from pydantic import BaseModel


@dataclass
class BedManning:
    name: str
    manning: float


SURFACE_MANNINGS = {
    "AS": BedManning("tarmacadam", 0.016),
    "BK": BedManning("brick", 0.015),
    "BR": BedManning("bedrock", 0.03),
    "CC": BedManning("concrete", 0.015),
    "CM": BedManning("corrugated metal", 0.05),
    "CO": BedManning("cobble", 0.04),
    "GA": BedManning("gabions", 0.03),
    "GR": BedManning("gravel", 0.035),
    "ME": BedManning("metal", 0.04),
    "MA": BedManning("masonry", 0.04),
    "OT": BedManning("other", 0.03),
    "PL": BedManning("plastic", 0.015),
    "PP": BedManning("plastic pile", 0.03),
    "RA": BedManning("rock armour", 0.03),
    "RR": BedManning("rip-rap", 0.03),
    "RU": BedManning("rubble", 0.05),
    "SO": BedManning("soil", 0.03),
    "SP": BedManning("sheet pile", 0.03),
    "ST": BedManning("stone", 0.025),
    "TA": BedManning("Tarmacadam", 0.016),
    "TI": BedManning("timber", 0.02),
    "WO": BedManning("wood", 0.05),
    "WP": BedManning("wood pile", 0.03),
}

VEGETATION_MANNINGS = {
    "FF": BedManning("free floating plants", 0.07),
    "GS": BedManning("Grass", 0.07),
    "MO": BedManning("moss", 0.07),
    "RE": BedManning("Reeds", 0.1),
    "MP": BedManning("submerged plants", 0.1),
    "TR": BedManning("Trailing plants", 0.1),
    "GL": BedManning("Grass", 0.05),
    "GM": BedManning("Grass", 0.035),
    "HC": BedManning("closed hedge", 0.07),
    "HO": BedManning("open hedge", 0.05),
    "TD": BedManning("Dense Trees", 0.1),
    "TH": BedManning("Heavy Trees", 0.1),
    "TL": BedManning("Light Trees", 0.05),
    "TM": BedManning("Medium Trees", 0.07),
    "NO": BedManning("", 0.0)
    # "GS": BedManning("Grass", 0.04), # vegetation types-banks & flood plain
}


@dataclass
class SectionRaw:
    metadata: dict[str, list[Optional[str]]]
    cross_sections: list[list[str]]


class CrossSection(BaseModel):
    offset: float
    level: float
    feature_code: str
    easting: float
    northing: float
    # From level last char
    left: Optional[bool]
    right: Optional[bool]

    @property
    def __feature_code_split(self) -> Optional[Tuple[str, str]]:
        codes = self.feature_code.strip("~*").split("*")
        if len(codes) != 2:
            return None
        return codes[0], codes[1]

    @property
    def surface(self) -> Optional[str]:
        return (
            self.__feature_code_split[0]
            if self.__feature_code_split is not None
            else None
        )

    @property
    def vegetation(self) -> Optional[str]:
        return (
            self.__feature_code_split[1]
            if self.__feature_code_split is not None
            else None
        )

    @classmethod
    def from_raw(cls, cross_raw: list[str]):

        if len(cross_raw) != 5:
            raise ValueError(f"input array must be length 5, got {len(cross_raw)}")

        offset = float(cross_raw[0])
        level_code = cross_raw[1]
        left: Optional[bool] = None

        if level_code[-1] == "L":
            left = True
        elif level_code[-1] == "R":
            left = False

        right = (not left) if left is not None else None

        # If we're on a bank point, remove that last character so we have a valid float
        level_str = level_code[:-1] if (left or right) else level_code

        return cls(
            offset=offset,
            level=float(level_str),
            feature_code=cross_raw[2],
            easting=float(cross_raw[3]),
            northing=float(cross_raw[4]),
            left=left,
            right=right,
        )


class Section(BaseModel):
    date: str
    cross_sections: list[CrossSection]
    section_number: str

    @property
    def river_num(self) -> int:
        number = self.section_number.split(".")[0]
        return int(number)

    chainage: float
    offset: float
    easting: float
    northing: float
    level: float
    ground: str

    @classmethod
    def from_raw(cls, section_raw: SectionRaw):
        cross_sections = [CrossSection.from_raw(x) for x in section_raw.cross_sections]
        date = section_raw.metadata["SECDATE"][0]
        offset = section_raw.metadata["SECBEARING"][0]
        newsec = section_raw.metadata["NEWSEC"]
        section_number = newsec[0]
        chainage = newsec[1]
        level = newsec[2]
        seccoords = section_raw.metadata["SECCOORDS"]
        easting = seccoords[0]
        northing = seccoords[1]
        ground = section_raw.metadata["BEDMATERIAL"][0]

        values = [
            date,
            section_number,
            chainage,
            offset,
            easting,
            northing,
            level,
        ]
        if any([x is None for x in values]):
            raise ValueError(f"Unexpected None found when parsing section: {values}")

        return cls(
            date=date,  # type: ignore
            cross_sections=cross_sections,
            section_number=section_number,  # type: ignore
            chainage=float(chainage),  # type: ignore
            offset=float(offset),  # type: ignore
            easting=float(easting),  # type: ignore
            northing=float(northing),  # type: ignore
            level=float(level),  # type: ignore
            ground=ground or "",
        )

    def __name(self, riv_name_map: dict[int, str]) -> str:
        short_name = riv_name_map[self.river_num]
        chainage = round(self.chainage)
        suffix = f"{chainage}".rjust(5, "0")
        return f"{short_name}.{suffix}"

    def __first_record(self, riv_name_map: dict[int, str]) -> str:
        return ",".join(
            [
                "WLEVEL",
                f"{self.section_number}",
                self.__name(riv_name_map),
                self.date,
                f"{self.chainage}",
                f"{self.offset}",
                f"{self.level}",
                f"{self.easting}",
                f"{self.northing}",
                "WATER",
                "",
                self.ground,
                "",
            ]
        )

    def __cross_section_record(
        self, riv_name_map: dict[int, str], cross_section: CrossSection
    ) -> str:

        bank: str
        if cross_section.left is None and cross_section.right is None:
            bank = ""
        else:
            bank = "LEFT" if cross_section.left else "RIGHT"

        is_vegetation = cross_section.vegetation != "NO"

        manning: Optional[float] = None

        if (
            cross_section.feature_code is not None
            and cross_section.vegetation is not None
            and cross_section.surface is not None
        ):
            manning = (
                VEGETATION_MANNINGS[cross_section.vegetation].manning
                if is_vegetation
                else SURFACE_MANNINGS[cross_section.surface].manning
            )

        return ",".join(
            [
                "BED",
                f"{self.section_number}",
                self.__name(riv_name_map),
                self.date,
                f"{self.chainage}",
                f"{cross_section.offset}",
                f"{cross_section.level}",
                f"{cross_section.easting}",
                f"{cross_section.northing}",
                bank,
                f"{manning}" if manning else "",
                SURFACE_MANNINGS[cross_section.surface].name
                if cross_section.surface
                else "",
                VEGETATION_MANNINGS[cross_section.vegetation].name
                if cross_section.vegetation
                else "",
            ]
        )

    def csv_records(self, riv_name_map: dict[int, str]) -> list[str]:
        records: list[str] = []
        records.append(self.__first_record(riv_name_map))

        for cross_section in self.cross_sections:
            records.append(self.__cross_section_record(riv_name_map, cross_section))

        return records
