from typing import Optional, Tuple

from pydantic import BaseModel, ConfigDict
from pydantic.dataclasses import dataclass


class BedManning(BaseModel):
    name: str
    manning: float
    model_config = ConfigDict(extra="forbid")


class Mannings(BaseModel):
    surface: dict[str, BedManning]
    vegetation: dict[str, BedManning]
    model_config = ConfigDict(extra="forbid")


_SURFACE_MANNINGS = {
    "AS": BedManning(name="tarmacadam", manning=0.016),
    "BK": BedManning(name="brick", manning=0.015),
    "BR": BedManning(name="bedrock", manning=0.03),
    "CC": BedManning(name="concrete", manning=0.015),
    "CM": BedManning(name="corrugated metal", manning=0.05),
    "CO": BedManning(name="cobble", manning=0.04),
    "GA": BedManning(name="gabions", manning=0.03),
    "GR": BedManning(name="gravel", manning=0.035),
    "ME": BedManning(name="metal", manning=0.04),
    "MA": BedManning(name="masonry", manning=0.04),
    "OT": BedManning(name="other", manning=0.03),
    "PL": BedManning(name="plastic", manning=0.015),
    "PP": BedManning(name="plastic pile", manning=0.03),
    "RA": BedManning(name="rock armour", manning=0.03),
    "RR": BedManning(name="rip-rap", manning=0.03),
    "RU": BedManning(name="rubble", manning=0.05),
    "SO": BedManning(name="soil", manning=0.03),
    "SP": BedManning(name="sheet pile", manning=0.03),
    "ST": BedManning(name="stone", manning=0.025),
    "TA": BedManning(name="Tarmacadam", manning=0.016),
    "TI": BedManning(name="timber", manning=0.02),
    "WO": BedManning(name="wood", manning=0.05),
    "WP": BedManning(name="wood pile", manning=0.03),
}

_VEGETATION_MANNINGS = {
    "FF": BedManning(name="free floating plants", manning=0.07),
    "GS": BedManning(name="Grass", manning=0.07),
    "MO": BedManning(name="moss", manning=0.07),
    "RE": BedManning(name="Reeds", manning=0.1),
    "MP": BedManning(name="submerged plants", manning=0.1),
    "TR": BedManning(name="Trailing plants", manning=0.1),
    "GL": BedManning(name="Grass", manning=0.05),
    "GM": BedManning(name="Grass", manning=0.035),
    "HC": BedManning(name="closed hedge", manning=0.07),
    "HO": BedManning(name="open hedge", manning=0.05),
    "TD": BedManning(name="Dense Trees", manning=0.1),
    "TH": BedManning(name="Heavy Trees", manning=0.1),
    "TL": BedManning(name="Light Trees", manning=0.05),
    "TM": BedManning(name="Medium Trees", manning=0.07),
    "NO": BedManning(name="", manning=0.0),
}

DEFAULT_MANNINGS = Mannings(
    surface=_SURFACE_MANNINGS,
    vegetation=_VEGETATION_MANNINGS,
)


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
    def from_raw(cls, cross_raw: list[str], mannings: Mannings):

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

        cross_section = cls(
            offset=offset,
            level=float(level_str),
            feature_code=cross_raw[2],
            easting=float(cross_raw[3]),
            northing=float(cross_raw[4]),
            left=left,
            right=right,
        )

        if (
            cross_section.vegetation
            and mannings.vegetation.get(cross_section.vegetation) is None
        ):
            raise ValueError(
                f"Did not understand feature code '{cross_section.vegetation}' for vegation manning."
            )
        if (
            cross_section.surface
            and mannings.surface.get(cross_section.surface) is None
        ):
            raise ValueError(
                f"Did not understand feature code '{cross_section.surface}' for surface manning."
            )
        return cross_section


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
    def from_raw(cls, section_raw: SectionRaw, mannings: Mannings):
        cross_sections = [
            CrossSection.from_raw(x, mannings) for x in section_raw.cross_sections
        ]
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
        self,
        riv_name_map: dict[int, str],
        cross_section: CrossSection,
        mannings: Mannings,
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
                mannings.vegetation[cross_section.vegetation].manning
                if is_vegetation
                else mannings.surface[cross_section.surface].manning
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
                (
                    mannings.surface[cross_section.surface].name
                    if cross_section.surface
                    else ""
                ),
                (
                    mannings.vegetation[cross_section.vegetation].name
                    if cross_section.vegetation
                    else ""
                ),
            ]
        )

    def csv_records(
        self,
        riv_name_map: dict[int, str],
        mannings: Mannings,
    ) -> list[str]:
        records: list[str] = []
        records.append(self.__first_record(riv_name_map))

        for cross_section in self.cross_sections:
            records.append(
                self.__cross_section_record(
                    riv_name_map,
                    cross_section,
                    mannings,
                )
            )

        return records
