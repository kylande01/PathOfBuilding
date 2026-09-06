import unittest

from unique_mod_id_patcher.gui_model import (
    AMBIGUOUS_UNIQUE,
    build_result_rows,
    collect_selected_replacements,
)
from unique_mod_id_patcher.models import (
    BlockAnalysis,
    ModMatch,
    ModMatchStatus,
    ModOccurrence,
    UniqueBlock,
    UniqueItem,
)


class GuiModelTests(unittest.TestCase):
    def test_builds_patchable_and_identity_issue_rows(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )
        replacement = ModMatch(
            occurrence=occurrence,
            status=ModMatchStatus.REPLACEMENT,
            candidate_ids=("NewMod",),
        )
        unique = UniqueItem(
            name="Example Boots",
            base_type="Iron Greaves",
            vestigial_observed=False,
            mods=(),
        )
        replacement_analysis = BlockAnalysis(
            block=UniqueBlock(
                name="Example Boots",
                start_line=5,
                lines=("Example Boots", "Iron Greaves", "OldMod"),
                variants=(),
            ),
            unique_candidates=(unique,),
            mod_matches=(replacement,),
        )
        ambiguous_analysis = BlockAnalysis(
            block=UniqueBlock(
                name="Ambiguous Boots",
                start_line=20,
                lines=("Ambiguous Boots", "Iron Greaves"),
                variants=(),
            ),
            unique_candidates=(unique, unique),
            mod_matches=(),
        )

        rows = build_result_rows(
            (replacement_analysis, ambiguous_analysis)
        )

        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].is_patchable)
        self.assertEqual(rows[0].proposed_mod_id, "NewMod")
        self.assertEqual(rows[1].status, AMBIGUOUS_UNIQUE)
        self.assertFalse(rows[1].is_patchable)

        selected_matches = collect_selected_replacements(
            rows,
            {rows[0].key, rows[1].key},
        )
        self.assertEqual(selected_matches, (replacement,))


if __name__ == "__main__":
    unittest.main()
