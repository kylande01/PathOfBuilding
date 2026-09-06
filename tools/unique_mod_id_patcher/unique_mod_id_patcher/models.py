from enum import Enum
from dataclasses import dataclass


class ModMatchStatus(Enum):
    ALREADY_CURRENT = "already_current"
    REPLACEMENT = "replacement"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"

@dataclass(frozen=True)
class ModStat:
    stat_id: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class UniqueMod:
    mod_group: str
    mod_id: str
    stats: tuple[ModStat, ...]


@dataclass(frozen=True)
class UniqueItem:
    name: str
    base_type: str
    vestigial_observed: bool
    mods: tuple[UniqueMod, ...]


@dataclass(frozen=True)
class UniqueDataset:
    league_name: str
    uniques: tuple[UniqueItem, ...]


@dataclass(frozen=True)
class UniqueBlock:
    name: str
    start_line: int
    lines: tuple[str, ...]
    variants: tuple[str, ...]


@dataclass(frozen=True)
class ModOccurrence:
    line_number: int
    raw_line: str
    mod_id: str
    id_start_index: int
    id_end_index: int
    variant_numbers: tuple[int, ...]


@dataclass(frozen=True)
class ModMatch:
    occurrence: ModOccurrence
    status: ModMatchStatus
    candidate_ids: tuple[str, ...]

@dataclass(frozen=True)
class BlockAnalysis:
    block: UniqueBlock
    unique_candidates: tuple[UniqueItem, ...]
    mod_matches: tuple[ModMatch, ...]