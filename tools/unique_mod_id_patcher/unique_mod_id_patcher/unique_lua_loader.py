import re
from pathlib import Path
from collections.abc import Collection

from .models import ModOccurrence, UniqueBlock

MOD_LINE_PATTERN = re.compile(
    r"^(?P<prefix>(?:\{[^{}\r\n]+\})*)"
    r"(?P<mod_id>[A-Za-z0-9_]+)"
    r"(?P<selectors>(?:\[-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?\])*)$"
)

VARIANT_TAG_PATTERN = re.compile(
    r"\{variant:(?P<numbers>\d+(?:,\d+)*)\}"
)

DECORATED_TEXT_PATTERN = re.compile(
    r"^(?P<prefix>(?:\{[^{}\r\n]+\})*)(?P<text>.+)$"
)


def _extract_variant_numbers(prefix: str) -> tuple[int, ...]:
    variant_match = VARIANT_TAG_PATTERN.search(prefix)

    if variant_match is None:
        return ()

    return tuple(
        int(number)
        for number in variant_match.group("numbers").split(",")
    )

def load_unique_blocks(path: Path) -> tuple[UniqueBlock, ...]:
    blocks: list[UniqueBlock] = []
    current_lines: list[str] | None = None
    current_start_line: int | None = None

    with path.open("r", encoding="utf-8") as input_file:
        for line_number, raw_line in enumerate(input_file, start=1):
            line = raw_line.rstrip("\r\n")
            marker = line.strip()

            if marker == "[[":
                if current_lines is not None:
                    raise ValueError(
                        f"Nested unique block on line {line_number}"
                    )

                current_lines = []
                current_start_line = line_number + 1
                continue

            if marker in {"]],[[", "]],", "]]", "]],}"}:
                if current_lines is None or current_start_line is None:
                    raise ValueError(
                        f"Unexpected block ending on line {line_number}"
                    )

                if not current_lines:
                    raise ValueError(
                        f"Empty unique block ending on line {line_number}"
                    )

                variant_names = tuple(
                        block_line.removeprefix("Variant: ")
                        for block_line in current_lines
                        if block_line.startswith("Variant: ")
                    )

                blocks.append(
                    UniqueBlock(
                        name=current_lines[0],
                        start_line=current_start_line,
                        lines=tuple(current_lines),
                        variants=variant_names,
                    )
                )

                if marker == "]],[[":
                    current_lines = []
                    current_start_line = line_number + 1
                else:
                    current_lines = None
                    current_start_line = None
                continue

            if current_lines is not None:
                current_lines.append(line)

    if current_lines is not None:
        raise ValueError("Unterminated unique block")

    return tuple(blocks)


def parse_mod_line(
        line: str,
        line_number: int,
) -> ModOccurrence | None:
    line_match = MOD_LINE_PATTERN.match(line)

    if line_match is None:
        return None

    prefix = line_match.group("prefix")
    variant_numbers = _extract_variant_numbers(prefix)

    id_start_index, id_end_index = line_match.span("mod_id")

    return ModOccurrence(
        line_number=line_number,
        raw_line=line,
        mod_id=line_match.group("mod_id"),
        id_start_index=id_start_index,
        id_end_index=id_end_index,
        variant_numbers=variant_numbers,
    )


def _variant_numbers_apply_to_current(
            block: UniqueBlock,
            variant_numbers: tuple[int, ...],
    ) -> bool:
        if not variant_numbers:
            return True

        current_variant_numbers = {
            variant_number
            for variant_number, variant_name in enumerate(
                block.variants,
                start=1,
            )
            if "current" in variant_name.casefold()
        }

        return any(
            variant_number in current_variant_numbers
            for variant_number in variant_numbers
        )


def find_mod_occurrences(
        block: UniqueBlock,
        known_mod_ids: Collection[str],
) -> tuple[ModOccurrence, ...]:
    occurrences: list[ModOccurrence] = []

    for offset, line in enumerate(block.lines):
        occurrence = parse_mod_line(
            line,
            line_number=block.start_line + offset,
        )

        if (
            occurrence is not None
            and occurrence.mod_id in known_mod_ids
        ):
            occurrences.append(occurrence)

    return tuple(occurrences)


def applies_to_current_variant(
    block: UniqueBlock,
    occurrence: ModOccurrence,
) -> bool:
    return _variant_numbers_apply_to_current(
        block,
        occurrence.variant_numbers,
    )


def find_current_base_types(
    block: UniqueBlock,
    known_base_types: Collection[str],
) -> tuple[str, ...]:
    current_base_types: list[str] = []

    for line in block.lines[1:]:
        line_match = DECORATED_TEXT_PATTERN.match(line)

        if line_match is None:
            continue

        base_type = line_match.group("text")

        if base_type not in known_base_types:
            continue

        variant_numbers = _extract_variant_numbers(
            line_match.group("prefix")
        )

        if _variant_numbers_apply_to_current(
            block,
            variant_numbers,
        ):
            current_base_types.append(base_type)

    return tuple(current_base_types)