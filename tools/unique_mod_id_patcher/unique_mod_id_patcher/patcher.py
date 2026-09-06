import os
import re
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile

from .models import ModMatch, ModMatchStatus, ModOccurrence


MOD_ID_PATTERN = re.compile(r"[A-Za-z0-9_]+")

def replace_mod_id_in_line(
        line: str,
        occurrence: ModOccurrence,
        replacement_id: str,
) -> str:
    if MOD_ID_PATTERN.fullmatch(replacement_id) is None:
        raise ValueError("Replacement ID is malformed")

    if line != occurrence.raw_line:
        raise ValueError("Source line changed after analysis")

    observed_mod_id = line[
        occurrence.id_start_index:occurrence.id_end_index
    ]

    if observed_mod_id != occurrence.mod_id:
        raise ValueError(
            "ID span does not match the parsed mod ID"
        )

    return (
        line[:occurrence.id_start_index]
        + replacement_id
        + line[occurrence.id_end_index:]
    )


def apply_mod_match_to_line(
        line: str,
        match: ModMatch,
) -> str:
    if match.status is not ModMatchStatus.REPLACEMENT:
        raise ValueError("Mod match is not a replacement")

    if len(match.candidate_ids) != 1:
        raise ValueError(
            "Replacement match must have exactly one candidate ID"
        )

    return replace_mod_id_in_line(
        line,
        match.occurrence,
        match.candidate_ids[0],
    )


def apply_mod_match_to_text(
        source_text: str,
        match: ModMatch,
) -> str:
    lines = source_text.splitlines(keepends=True)
    line_index = match.occurrence.line_number - 1

    if line_index < 0 or line_index >= len(lines):
        raise ValueError(
            "Mod occurrence line number is outside the source text"
        )

    source_line = lines[line_index]

    if source_line.endswith("\r\n"):
        line_body = source_line[:-2]
        line_ending = "\r\n"
    elif source_line.endswith("\n") or source_line.endswith("\r"):
        line_body = source_line[:-1]
        line_ending = source_line[-1:]
    else:
        line_body = source_line
        line_ending = ""

    patched_line = apply_mod_match_to_line(
        line_body,
        match,
    )
    lines[line_index] = patched_line + line_ending

    return "".join(lines)


def apply_mod_matches_to_text(
        source_text: str,
        matches: tuple[ModMatch, ...],
) -> str:
    target_line_numbers = tuple(
        match.occurrence.line_number
        for match in matches
    )

    if len(set(target_line_numbers)) != len(target_line_numbers):
        raise ValueError(
            "Batch contains multiple replacements for the same line"
        )

    patched_text = source_text

    for match in matches:
        patched_text = apply_mod_match_to_text(
            patched_text,
            match,
        )

    return patched_text


def write_mod_matches_to_file(
        path: Path,
        matches: tuple[ModMatch, ...],
) -> str:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as source_file:
        source_text = source_file.read()

    patched_text = apply_mod_matches_to_text(
        source_text,
        matches,
    )

    if patched_text == source_text:
        return source_text

    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix="tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(patched_text)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        with temporary_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as verification_file:
            if verification_file.read() != patched_text:
                raise OSError(
                    "Temporary patch file failed verification"
                )

        shutil.copymode(path, temporary_path)
        os.replace(temporary_path, path)

    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise

    return patched_text