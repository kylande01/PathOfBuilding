from pathlib import Path
import unittest

from unique_mod_id_patcher.unique_lua_loader import (
    applies_to_current_variant,
    find_current_base_types,
    find_mod_occurrences,
    load_unique_blocks,
    parse_mod_line,
)


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "minimal_unique_blocks.lua"
)
VARIANT_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "unique_blocks_with_variants.lua"
)


class UniqueLuaLoaderTests(unittest.TestCase):
    def test_loads_unique_blocks_with_source_positions(self) -> None:
        blocks = load_unique_blocks(FIXTURE_PATH)

        self.assertEqual(len(blocks), 2)

        first = blocks[0]
        self.assertEqual(first.name, "First Boots")
        self.assertEqual(first.start_line, 6)
        self.assertEqual(
            first.lines,
            (
                "First Boots",
                "Iron Greaves",
                "Requires Level 1",
                "FirstMod",
            ),
        )

        second = blocks[1]
        self.assertEqual(second.name, "Second Boots")
        self.assertEqual(second.start_line, 11)
        self.assertEqual(
            second.lines,
            (
                "Second Boots",
                "Wool Shoes",
                "SecondMod",
            ),
        )

    def test_collects_variant_names_in_lua_order(self) -> None:
        blocks = load_unique_blocks(VARIANT_FIXTURE_PATH)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(
            blocks[0].variants,
            (
                "Pre 3.20.0",
                "Current",
            ),
        )

    def test_parses_decorated_mod_line_and_preserves_its_span(self) -> None:
        line = "{variant:2}MovementVelocityUniqueBootsDexInt4[20,20]"

        occurrence = parse_mod_line(line, line_number=17)

        self.assertIsNotNone(occurrence)
        self.assertEqual(occurrence.line_number, 17)
        self.assertEqual(occurrence.raw_line, line)
        self.assertEqual(
            occurrence.mod_id,
            "MovementVelocityUniqueBootsDexInt4"
        )
        self.assertEqual(occurrence.variant_numbers, (2,))
        self.assertEqual(
            line[occurrence.id_start_index:occurrence.id_end_index],
            occurrence.mod_id
        )
        self.assertEqual(
            line[:occurrence.id_start_index],
            "{variant:2}",
        )
        self.assertEqual(
            line[occurrence.id_end_index:],
            "[20,20]",
        )

    def test_finds_known_mod_occurrences_in_a_block(self) -> None:
        blocks = load_unique_blocks(VARIANT_FIXTURE_PATH)

        occurrences = find_mod_occurrences(
            blocks[0],
            known_mod_ids={"OldMod", "CurrentMod"},
        )

        self.assertEqual(len(occurrences), 2)
        self.assertEqual(
            tuple(occurrence.mod_id for occurrence in occurrences),
            ("OldMod", "CurrentMod"),
        )
        self.assertEqual(
            tuple(occurrence.line_number for occurrence in occurrences),
            (8, 9),
        )
        self.assertEqual(occurrences[0].variant_numbers, (1,))
        self.assertEqual(occurrences[1].variant_numbers, (2,))


    def test_identifies_mods_that_apply_to_current_variants(self) -> None:
        block = load_unique_blocks(VARIANT_FIXTURE_PATH)[0]

        occurrences = find_mod_occurrences(
            block,
            known_mod_ids={"OldMod", "CurrentMod", "SharedMod"},
        )
        occurrences_by_id = {
            occurrence.mod_id: occurrence
            for occurrence in occurrences
        }

        self.assertFalse(
            applies_to_current_variant(
                block,
                occurrences_by_id["OldMod"],
            )
        )
        self.assertTrue(
            applies_to_current_variant(
                block,
                occurrences_by_id["CurrentMod"],
            )
        )
        self.assertTrue(
            applies_to_current_variant(
                block,
                occurrences_by_id["SharedMod"],
            )
        )

    def test_finds_base_types_that_apply_to_current_variant(self) -> None:
        ordinary_block = load_unique_blocks(FIXTURE_PATH)[0]
        variant_block = load_unique_blocks(VARIANT_FIXTURE_PATH)[0]

        ordinary_base_types = find_current_base_types(
            ordinary_block,
            known_base_types={"Iron Greaves", "Titan Greaves"},
        )
        variant_base_types = find_current_base_types(
            variant_block,
            known_base_types={"Iron Greaves", "Titan Greaves"},
        )

        self.assertEqual(
            ordinary_base_types,
            ("Iron Greaves",),
        )
        self.assertEqual(
            variant_base_types,
            ("Titan Greaves",),
        )

if __name__ == "__main__":
    unittest.main()