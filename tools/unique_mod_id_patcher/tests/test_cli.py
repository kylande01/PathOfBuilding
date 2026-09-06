from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import unittest

from unique_mod_id_patcher.cli import main
from tempfile import TemporaryDirectory

FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"


class CliTests(unittest.TestCase):
    def test_prints_analysis_report(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "--dataset",
                    str(FIXTURE_DIRECTORY / "minimal_uniques.json"),
                    "--mod-text",
                    str(
                        FIXTURE_DIRECTORY
                        / "minimal_mod_item_exclusive.lua"
                    ),
                    "--unique-lua",
                    str(
                        FIXTURE_DIRECTORY
                        / "analysis_unique_blocks.lua"
                    ),
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Blocks analyzed: 1", output.getvalue())
        self.assertIn(
            "Already-current mods: 1",
            output.getvalue(),
        )

    def test_write_option_applies_all_safe_replacements(self) -> None:
        source_fixture = (
            FIXTURE_DIRECTORY
            / "replacement_unique_blocks.lua"
        )

        with TemporaryDirectory() as temporary_directory:
            target_path = (
                Path(temporary_directory)
                / "replacement_unique_blocks.lua"
            )
            original_bytes = source_fixture.read_bytes()
            target_path.write_bytes(original_bytes)

            output = StringIO()

            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--dataset",
                        str(
                            FIXTURE_DIRECTORY
                            / "minimal_uniques.json"
                        ),
                        "--mod-text",
                        str(
                            FIXTURE_DIRECTORY
                            / "replacement_mod_item_exclusive.lua"
                        ),
                        "--unique-lua",
                        str(target_path),
                        "--write",
                    ]
                )

            expected_bytes = original_bytes.replace(
                b"OldMovementMod",
                b"MovementVelocityUnique__7",
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                target_path.read_bytes(),
                expected_bytes,
            )
            self.assertIn(
                "Wrote 1 replacement",
                output.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()