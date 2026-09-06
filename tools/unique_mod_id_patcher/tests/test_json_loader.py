from pathlib import Path
import unittest

from unique_mod_id_patcher.json_loader import load_unique_dataset

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_PATH = FIXTURES_DIR / "minimal_uniques.json"
MISSING_UNIQUES_PATH = FIXTURES_DIR / "missing_uniques.json"
WRONG_UNIQUES_TYPE_PATH = FIXTURES_DIR / "wrong_uniques_type.json"


class JsonLoaderTests(unittest.TestCase):
    def test_loads_minimal_dataset(self) -> None:
        dataset = load_unique_dataset(FIXTURE_PATH)

        self.assertEqual(dataset.league_name, "Fixture")
        self.assertEqual(len(dataset.uniques), 1)

        unique = dataset.uniques[0]
        self.assertEqual(unique.name, "Abberath's Hooves")
        self.assertEqual(unique.base_type, "Goathide Boots")
        self.assertTrue(unique.vestigial_observed)
        self.assertEqual(len(unique.mods), 2)

        movement_mod = unique.mods[0]
        self.assertEqual(movement_mod.mod_group, "explicit")
        self.assertEqual(movement_mod.mod_id, "MovementVelocityUnique__7")
        self.assertEqual(len(movement_mod.stats), 1)

        movement_stat = movement_mod.stats[0]
        self.assertEqual(movement_stat.stat_id, "base_movement_velocity_+%")
        self.assertEqual(movement_stat.minimum, 15.0)
        self.assertEqual(movement_stat.maximum, 15.0)

        empty_mod = unique.mods[1]
        self.assertEqual(empty_mod.mod_id, "EmptyStatsFixture")
        self.assertEqual(len(empty_mod.stats), 0)

    def test_rejects_dataset_without_uniques(self) -> None:
        with self.assertRaisesRegex(ValueError, "uniques"):
            load_unique_dataset(MISSING_UNIQUES_PATH)

    def test_rejects_non_list_uniques(self) -> None:
        with self.assertRaisesRegex(ValueError, "uniques.*list"):
            load_unique_dataset(WRONG_UNIQUES_TYPE_PATH)


if __name__ == "__main__":
    unittest.main()