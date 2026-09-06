from pathlib import Path
import unittest

from unique_mod_id_patcher.mod_text_loader import load_mod_texts


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "minimal_mod_item_exclusive.lua"
)
DUPLICATE_MOD_IDS_PATH = (
    Path(__file__).parent / "fixtures" / "duplicate_mod_ids.lua"
)
NO_MOD_ENTRIES_PATH = (
    Path(__file__).parent / "fixtures" / "no_mod_entries.lua"
)
MALFORMED_MOD_ENTRIES_PATH = (
    Path(__file__).parent / "fixtures" / "malformed_mod_entries.lua"
)
TYPE_PREFIXED_MOD_ENTRY_PATH = (
    Path(__file__).parent / "fixtures" / "type_prefixed_mod_entry.lua"
)

class ModTextLoaderTests(unittest.TestCase):
    def test_loads_single_and_multi_stat_entries(self) -> None:
        mod_texts = load_mod_texts(FIXTURE_PATH)

        self.assertEqual(len(mod_texts), 2)

        self.assertEqual(
            mod_texts["MovementVelocityUnique__7"],
            ("15% increased Movement Speed",),
        )
        self.assertEqual(
            mod_texts["LocalBaseArmourAndEvasionRatingUnique__1"],
            (
                "+(50-100) to Armour",
                "+(50-100) to Evasion Rating",
            ),
        )

    def test_rejects_duplicate_mod_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "DuplicateMod"):
            load_mod_texts(DUPLICATE_MOD_IDS_PATH)

    def test_rejects_file_without_mod_entries(self) -> None:
        with self.assertRaisesRegex(ValueError, "mod entries"):
            load_mod_texts(NO_MOD_ENTRIES_PATH)

    def test_rejects_malformed_mod_entries(self) -> None:
        with self.assertRaisesRegex(ValueError, "Malformed mod entry"):
            load_mod_texts(MALFORMED_MOD_ENTRIES_PATH)

    def test_loads_entry_with_type_before_affix(self) -> None:
        mod_texts = load_mod_texts(TYPE_PREFIXED_MOD_ENTRY_PATH)

        self.assertEqual(
            mod_texts["MaximumLifeIncreasePercent2ElderItemsUnique__1"],
            (
                "(10-15)% increased maximum Life "
                "if 2 Elder Items are Equipped",
            ),
        )

if __name__ == "__main__":
    unittest.main()