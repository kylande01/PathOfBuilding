from pathlib import Path
import unittest

from unique_mod_id_patcher.json_loader import load_unique_dataset
from unique_mod_id_patcher.matcher import (
    analyze_unique_blocks,
    analyze_unique_block,
    classify_mod_match,
    find_mod_id_candidates,
    find_unique_candidates,
    index_uniques_by_identity,
    match_block_mods,
)

from unique_mod_id_patcher.models import (
    ModMatchStatus,
    ModOccurrence,
    UniqueDataset,
    UniqueItem,
    UniqueMod,
)
from unique_mod_id_patcher.unique_lua_loader import load_unique_blocks


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "minimal_uniques.json"
)
VARIANT_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "unique_blocks_with_variants.lua"
)

class MatcherTests(unittest.TestCase):
    def test_indexes_uniques_by_name_and_base_type(self) -> None:
        dataset = load_unique_dataset(FIXTURE_PATH)

        index = index_uniques_by_identity(dataset)

        identity = ("Abberath's Hooves", "Goathide Boots")

        self.assertIn(identity, index)
        self.assertEqual(
            index[identity],
            (dataset.uniques[0],),
        )

    def test_finds_candidate_using_current_base_type(self) -> None:
        historical_unique = UniqueItem(
            name="Variant Boots",
            base_type="Iron Greaves",
            vestigial_observed=False,
            mods=(),
        )
        current_unique = UniqueItem(
            name="Variant Boots",
            base_type="Titan Greaves",
            vestigial_observed=False,
            mods=(),
        )
        unrelated_unique = UniqueItem(
            name="Other Boots",
            base_type="Titan Greaves",
            vestigial_observed=False,
            mods=(),
        )
        dataset = UniqueDataset(
            league_name="Fixture",
            uniques=(
                historical_unique,
                current_unique,
                unrelated_unique,
            ),
        )

        block = load_unique_blocks(VARIANT_FIXTURE_PATH)[0]
        unique_index = index_uniques_by_identity(dataset)

        candidates = find_unique_candidates(
            block,
            unique_index,
        )

        self.assertEqual(candidates, (current_unique,))

    def test_finds_mod_id_candidate_with_identical_stat_text(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )
        unique = UniqueItem(
            name="Example Boots",
            base_type="Iron Greaves",
            vestigial_observed=False,
            mods=(
                UniqueMod(
                    mod_group="explicit",
                    mod_id="NewMod",
                    stats=(),
                ),
                UniqueMod(
                    mod_group="explicit",
                    mod_id="DifferentMod",
                    stats=(),
                ),
            ),
        )
        mod_texts = {
            "OldMod": ("15% increased Movement Speed",),
            "NewMod": ("15% increased Movement Speed",),
            "DifferentMod": ("+20 to maximum Life",),
        }

        candidates = find_mod_id_candidates(
            occurrence,
            unique,
            mod_texts,
        )

        self.assertEqual(candidates, ("NewMod",))

    def test_classifies_one_different_candidate_as_replacement(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )

        match = classify_mod_match(
            occurrence,
            candidate_ids=("NewMod",),
        )

        self.assertEqual(match.occurrence, occurrence)
        self.assertEqual(match.status, ModMatchStatus.REPLACEMENT)
        self.assertEqual(match.candidate_ids, ("NewMod",))

    def test_classifies_authoritative_existing_id_as_current(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )

        match = classify_mod_match(
            occurrence,
            candidate_ids=("OldMod",),
        )

        self.assertEqual(match.status, ModMatchStatus.ALREADY_CURRENT)
        self.assertEqual(match.candidate_ids, ("OldMod",))

    def test_classifies_no_candidates_as_unresolved(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )

        match = classify_mod_match(
            occurrence,
            candidate_ids=(),
        )

        self.assertEqual(match.status, ModMatchStatus.UNRESOLVED)
        self.assertEqual(match.candidate_ids, ())

    def test_classifies_multiple_candidates_as_ambiguous(self) -> None:
        occurrence = ModOccurrence(
            line_number=10,
            raw_line="OldMod",
            mod_id="OldMod",
            id_start_index=0,
            id_end_index=6,
            variant_numbers=(),
        )

        match = classify_mod_match(
            occurrence,
            candidate_ids=("NewMod", "OtherMod"),
        )

        self.assertEqual(match.status, ModMatchStatus.AMBIGUOUS)
        self.assertEqual(
            match.candidate_ids,
            ("NewMod", "OtherMod"),
        )

    def test_matches_only_mods_that_apply_to_current_variant(self) -> None:
        block = load_unique_blocks(VARIANT_FIXTURE_PATH)[0]

        unique = UniqueItem(
            name="Variant Boots",
            base_type="Titan Greaves",
            vestigial_observed=False,
            mods=(
                UniqueMod(
                    mod_group="explicit",
                    mod_id="NewOldMod",
                    stats=(),
                ),
                UniqueMod(
                    mod_group="explicit",
                    mod_id="CurrentMod",
                    stats=(),
                ),
                UniqueMod(
                    mod_group="explicit",
                    mod_id="NewSharedMod",
                    stats=(),
                ),
            ),
        )
        mod_texts = {
            "OldMod": ("Old text",),
            "NewOldMod": ("Old text",),
            "CurrentMod": ("Current text",),
            "SharedMod": ("Shared text",),
            "NewSharedMod": ("Shared text",),
        }

        matches = match_block_mods(
            block,
            unique,
            mod_texts,
        )

        self.assertEqual(
            tuple(match.occurrence.mod_id for match in matches),
            ("CurrentMod", "SharedMod"),
        )
        self.assertEqual(
            tuple(match.status for match in matches),
            (
                ModMatchStatus.ALREADY_CURRENT,
                ModMatchStatus.REPLACEMENT,
            ),
        )
        self.assertEqual(
            matches[1].candidate_ids,
            ("NewSharedMod",),
        )

    def test_does_not_match_mods_for_ambiguous_unique_identity(self) -> None:
        block = load_unique_blocks(VARIANT_FIXTURE_PATH)[0]

        first_candidate = UniqueItem(
            name="Variant Boots",
            base_type="Titan Greaves",
            vestigial_observed=False,
            mods=(),
        )
        second_candidate = UniqueItem(
            name="Variant Boots",
            base_type="Titan Greaves",
            vestigial_observed=True,
            mods=(),
        )
        dataset = UniqueDataset(
            league_name="Fixture",
            uniques=(
                first_candidate,
                second_candidate,
            ),
        )
        unique_index = index_uniques_by_identity(dataset)

        analysis = analyze_unique_block(
            block,
            unique_index,
            mod_texts={
                "CurrentMod": ("Current text",),
            },
        )

        self.assertEqual(
            analysis.unique_candidates,
            (first_candidate, second_candidate),
        )
        self.assertEqual(analysis.mod_matches, ())

    def test_analyzes_every_unique_block_in_a_file(self) -> None:
        blocks = load_unique_blocks(FIXTURE_PATH.parent / "minimal_unique_blocks.lua")

        first_unique = UniqueItem(
            name="First Boots",
            base_type="Iron Greaves",
            vestigial_observed=False,
            mods=(
                UniqueMod(
                    mod_group="explicit",
                    mod_id="FirstMod",
                    stats=(),
                ),
            ),
        )
        dataset = UniqueDataset(
            league_name="Fixture",
            uniques=(first_unique,),
        )
        unique_index = index_uniques_by_identity(dataset)
        mod_texts = {
            "FirstMod": ("First text",),
            "SecondMod": ("Second text",),
        }

        analyses = analyze_unique_blocks(
            blocks,
            unique_index,
            mod_texts,
        )

        self.assertEqual(len(analyses), 2)

        self.assertEqual(
            analyses[0].unique_candidates,
            (first_unique,),
        )
        self.assertEqual(
            analyses[0].mod_matches[0].status,
            ModMatchStatus.ALREADY_CURRENT,
        )

        self.assertEqual(analyses[1].unique_candidates, ())
        self.assertEqual(analyses[1].mod_matches, ())


if __name__ == "__main__":
    unittest.main()