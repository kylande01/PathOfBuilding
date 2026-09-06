import re
from pathlib import Path


ENTRY_PATTERN = re.compile(
    r'^\s*\["(?P<mod_id>[^"]+)"\]\s*=\s*\{\s*'
    r'(?:type\s*=\s*"[^"]+"\s*,\s*)?'
    r'affix\s*=\s*"[^"]*"\s*'
    r'(?P<stat_section>.*?),\s*statOrder\s*='
)
ENTRY_PREFIX_PATTERN = re.compile(r'^\s*\["')

STAT_TEXT_PATTERN = re.compile(r'"([^"]*)"')

def load_mod_texts(path: Path) -> dict[str, tuple[str, ...]]:
    mod_texts: dict[str, tuple[str, ...]] = {}

    with path.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            entry_match = ENTRY_PATTERN.match(line)

            if entry_match is None:
                if ENTRY_PREFIX_PATTERN.match(line):
                    raise ValueError(
                        f"Malformed mod entry on line {line_number}"
                    )
                continue

            mod_id = entry_match.group("mod_id")
            stat_section = entry_match.group("stat_section")
            stats_texts = tuple(STAT_TEXT_PATTERN.findall(stat_section))

            if mod_id in mod_texts:
                raise ValueError(f"Duplicate mod ID: {mod_id}")

            mod_texts[mod_id] = stats_texts

    if not mod_texts:
        raise ValueError("No mod entries found")

    return mod_texts