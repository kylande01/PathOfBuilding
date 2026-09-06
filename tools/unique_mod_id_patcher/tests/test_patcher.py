import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from unique_mod_id_patcher.patcher import (
    write_mod_matches_to_file,
    apply_mod_matches_to_text,
    apply_mod_match_to_line,
    apply_mod_match_to_text,
    replace_mod_id_in_line,
)
from unique_mod_id_patcher.unique_lua_loader import parse_mod_line
from unique_mod_id_patcher.models import (
    ModMatch,
    ModMatchStatus,
    ModOccurrence,
)


class PatcherTests(unittest.TestCase):
    def test_replaces_only_mod_id_in_decorated_line(self) -> None:
        line = "{variant:2}OldMod[20,20]"
        occurrence = parse_mod_line(line, line_number=17)

        self.assertIsNotNone(occurrence)
        assert occurrence is not None

        patched_line = replace_mod_id_in_line(
            line,
            occurrence,
            replacement_id="NewMod",
        )

        self.assertEqual(
            patched_line,
            "{variant:2}NewMod[20,20]",
        )

    def test_rejects_a_source_line_that_changed_after_analysis(self) -> None:
        original_line = "{variant:2}OldMod[20,20]"
        occurrence = parse_mod_line(
            original_line,
            line_number=10,
        )

        assert occurrence is not None

        changed_line = "{variant:2}SomeoneElse[20,20]"

        with self.assertRaisesRegex(ValueError, "Source line"):
            replace_mod_id_in_line(
                changed_line,
                occurrence,
                "NewMod",
            )

    def test_rejects_an_invalid_mod_id_span(self) -> None:
        line = "{variant:2}OldMod[20,20]"
        occurrence = ModOccurrence(
            line_number=10,
            raw_line=line,
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(2,),
        )

        with self.assertRaisesRegex(ValueError, "ID span"):
            replace_mod_id_in_line(
                line,
                occurrence,
                "NewMod",
            )

    def test_rejects_an_invalid_replacement_id(self) -> None:
        line = "{variant:2}OldMod[20,20]"
        occurrence = parse_mod_line(line, line_number=10)

        assert occurrence is not None

        with self.assertRaisesRegex(ValueError, "Replacement ID"):
            replace_mod_id_in_line(
                line,
                occurrence,
                "NewMod\nInjectedLine",
            )

    def test_applies_a_classified_replacement_to_a_line(self) -> None:
        line = "{variant:2}OldMod[20,20]"
        occurrence = parse_mod_line(line, line_number=10)

        assert occurrence is not None

        match = ModMatch(
            occurrence=occurrence,
            status=ModMatchStatus.REPLACEMENT,
            candidate_ids=("NewMod",),
        )

        patched_line = apply_mod_match_to_line(line, match)

        self.assertEqual(
            patched_line,
            "{variant:2}NewMod[20,20]",
        )

    def test_refuses_to_apply_an_already_current_match(self) -> None:
        line = "CurrentMod"
        occurrence = parse_mod_line(line, line_number=10)

        assert occurrence is not None

        match = ModMatch(
            occurrence=occurrence,
            status=ModMatchStatus.ALREADY_CURRENT,
            candidate_ids=("CurrentMod",),
        )

        with self.assertRaisesRegex(
            ValueError,
            "not a replacement",
        ):
            apply_mod_match_to_line(line, match)

    def test_refuses_replacement_with_multiple_candidates(self) -> None:
        line = "OldMod"
        occurrence = parse_mod_line(line, line_number=10)

        assert occurrence is not None

        match = ModMatch(
            occurrence=occurrence,
            status=ModMatchStatus.REPLACEMENT,
            candidate_ids=("NewMod", "OtherMod"),
        )

        with self.assertRaisesRegex(
            ValueError,
            "exactly one candidate",
        ):
            apply_mod_match_to_line(line, match)

    def test_applies_one_match_without_changing_line_endings(self) -> None:
        source_text = (
            "return {\r\n"
            "[[\r\n"
            "Example Boots\r\n"
            "{variant:2}OldMod[20,20]\r\n"
            "]],\r\n"
            "}\r\n"
        )
        line = "{variant:2}OldMod[20,20]"
        occurrence = parse_mod_line(line, line_number=4)

        assert occurrence is not None

        match = ModMatch(
            occurrence=occurrence,
            status=ModMatchStatus.REPLACEMENT,
            candidate_ids=("NewMod",),
        )

        patched_text = apply_mod_match_to_text(
            source_text,
            match,
        )

        self.assertEqual(
            patched_text,
            (
                "return {\r\n"
                "[[\r\n"
                "Example Boots\r\n"
                "{variant:2}NewMod[20,20]\r\n"
                "]],\r\n"
                "}\r\n"
            ),
        )

    def test_applies_multiple_replacements_as_one_batch(self) -> None:
        source_text = (
            "OldFirst\r\n"
            "OldSecond\r\n"
        )

        first_occurrence = parse_mod_line(
            "OldFirst",
            line_number=1,
        )
        second_occurrence = parse_mod_line(
            "OldSecond",
            line_number=2,
        )

        assert first_occurrence is not None
        assert second_occurrence is not None

        matches = (
            ModMatch(
                occurrence=first_occurrence,
                status=ModMatchStatus.REPLACEMENT,
                candidate_ids=("NewFirst",),
            ),
            ModMatch(
                occurrence=second_occurrence,
                status=ModMatchStatus.REPLACEMENT,
                candidate_ids=("NewSecond",),
            ),
        )

        patched_text = apply_mod_matches_to_text(
            source_text,
            matches,
        )

        self.assertEqual(
            patched_text,
            (
                "NewFirst\r\n"
                "NewSecond\r\n"
            ),
        )

    def test_writes_batch_to_file_and_preserves_crlf(self) -> None:
        source_bytes = b"OldFirst\r\nOldSecond\r\n"

        first_occurrence = parse_mod_line(
            "OldFirst",
            line_number=1,
        )
        second_occurrence = parse_mod_line(
            "OldSecond",
            line_number=2,
        )

        assert first_occurrence is not None
        assert second_occurrence is not None

        matches = (
            ModMatch(
                occurrence=first_occurrence,
                status=ModMatchStatus.REPLACEMENT,
                candidate_ids=("NewFirst",),
            ),
            ModMatch(
                occurrence=second_occurrence,
                status=ModMatchStatus.REPLACEMENT,
                candidate_ids=("NewSecond",),
            ),
        )

        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "boots.lua"
            path.write_bytes(source_bytes)

            write_mod_matches_to_file(path, matches)

            self.assertEqual(
                path.read_bytes(),
                b"NewFirst\r\nNewSecond\r\n",
            )


if __name__ == "__main__":
    unittest.main()