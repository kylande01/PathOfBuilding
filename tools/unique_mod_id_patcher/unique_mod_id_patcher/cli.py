import argparse
from collections.abc import Sequence
from pathlib import Path

from .report import format_analysis_report
from .workflow import analyze_files
from .models import ModMatchStatus
from .patcher import write_mod_matches_to_file


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze PoB unique mod IDs."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
        help="Path to the authoritative uniques JSON file.",
    )
    parser.add_argument(
        "--mod-text",
        required=True,
        type=Path,
        help="Path to ModItemExclusive.lua.",
    )
    parser.add_argument(
        "--unique-lua",
        required=True,
        type=Path,
        help="Path to a unique export Lua file."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply every safe replacement to the selected Lua file."
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    parsed_arguments = parser.parse_args(arguments)

    analyses = analyze_files(
        dataset_path=parsed_arguments.dataset,
        mod_text_path=parsed_arguments.mod_text,
        unique_lua_path=parsed_arguments.unique_lua,
    )

    print(format_analysis_report(analyses))

    if parsed_arguments.write:
        replacement_matches = tuple(
            match
            for analysis in analyses
            for match in analysis.mod_matches
            if match.status is ModMatchStatus.REPLACEMENT
        )

        if replacement_matches:
            write_mod_matches_to_file(
                parsed_arguments.unique_lua,
                replacement_matches,
            )

            replacement_word = (
                "replacement"
                if len(replacement_matches) == 1
                else "replacements"
            )
            print(
                f"Wrote {len(replacement_matches)} "
                f"{replacement_word} to "
                f"{parsed_arguments.unique_lua}"
            )
        else:
            print("No replacements to write.")

    return 0