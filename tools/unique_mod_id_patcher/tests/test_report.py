from pathlib import Path
import unittest

from unique_mod_id_patcher.report import format_analysis_report
from unique_mod_id_patcher.workflow import analyze_files
from unique_mod_id_patcher.models import (
    BlockAnalysis,
    ModMatch,
    ModMatchStatus,
    ModOccurrence,
    UniqueBlock,
)


FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"


class ReportTests(unittest.TestCase):
    def test_reports_analysis_totals(self) -> None:
        analyses = analyze_files(
            dataset_path=FIXTURE_DIRECTORY / "minimal_uniques.json",
            mod_text_path=(
                FIXTURE_DIRECTORY
                / "minimal_mod_item_exclusive.lua"
            ),
            unique_lua_path=(
                FIXTURE_DIRECTORY
                / "analysis_unique_blocks.lua"
            ),
        )

        report = format_analysis_report(analyses)

        self.assertIn("Blocks analyzed: 1", report)
        self.assertIn("Exact unique identities: 1", report)
        self.assertIn("Unmatched unique identities: 0", report)
        self.assertIn("Ambiguous unique identities: 0", report)
        self.assertIn("Already-current mods: 1", report)
        self.assertIn("Replacement candidates: 0", report)
        self.assertIn("Unresolved mods: 0", report)
        self.assertIn("Ambiguous mods: 0", report)

    def test_reports_replacement_line_and_ids(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )
        match = ModMatch(
            occurrence=occurrence,
            status=ModMatchStatus.REPLACEMENT,
            candidate_ids=("NewMod",),
        )
        analysis = BlockAnalysis(
            block=UniqueBlock(
                name="Example Boots",
                start_line=5,
                lines=("Example Boots", "OldMod"),
                variants=(),
            ),
            unique_candidates=(),
            mod_matches=(match,),
        )

        report = format_analysis_report((analysis,))

        self.assertIn(
            "Replacement line 10: OldMod -> NewMod",
            report,
        )

    def test_reports_mods_that_require_manual_review(self) -> None:
        unresolved = ModMatch(
            occurrence=ModOccurrence(
                line_number=11,
                raw_line="UnknownMod",
                mod_id="UnknownMod",
                id_start_index=0,
                id_end_index=10,
                variant_numbers=(),
            ),
            status=ModMatchStatus.UNRESOLVED,
            candidate_ids=(),
        )
        ambiguous = ModMatch(
            occurrence=ModOccurrence(
                line_number=12,
                raw_line="OldMod",
                mod_id="OldMod",
                id_start_index=0,
                id_end_index=6,
                variant_numbers=(),
            ),
            status=ModMatchStatus.AMBIGUOUS,
            candidate_ids=("FirstCandidate", "SecondCandidate"),
        )
        analysis = BlockAnalysis(
            block=UniqueBlock(
                name="Example Boots",
                start_line=5,
                lines=("Example Boots",),
                variants=(),
            ),
            unique_candidates=(),
            mod_matches=(unresolved, ambiguous),
        )

        report = format_analysis_report((analysis,))

        self.assertIn(
            "Unresolved line 11: UnknownMod",
            report,
        )
        self.assertIn(
            (
                "Ambiguous line 12: OldMod -> "
                "FirstCandidate, SecondCandidate"
            ),
            report,
        )

if __name__ == "__main__":
    unittest.main()