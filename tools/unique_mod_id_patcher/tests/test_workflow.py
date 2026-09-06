from pathlib import Path
import unittest

from unique_mod_id_patcher.models import ModMatchStatus
from unique_mod_id_patcher.workflow import analyze_files


FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"


class WorkflowTests(unittest.TestCase):
    def test_analyzes_three_input_files_together(self) -> None:
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

        self.assertEqual(len(analyses), 1)

        analysis = analyses[0]
        self.assertEqual(
            analysis.block.name,
            "Abberath's Hooves",
        )
        self.assertEqual(len(analysis.unique_candidates), 1)
        self.assertEqual(len(analysis.mod_matches), 1)
        self.assertEqual(
            analysis.mod_matches[0].status,
            ModMatchStatus.ALREADY_CURRENT,
        )


if __name__ == "__main__":
    unittest.main()