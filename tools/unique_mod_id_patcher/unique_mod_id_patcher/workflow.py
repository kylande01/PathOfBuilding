from pathlib import Path

from .json_loader import load_unique_dataset
from .matcher import (
    analyze_unique_blocks,
    index_uniques_by_identity,
)
from .models import BlockAnalysis
from .mod_text_loader import load_mod_texts
from .unique_lua_loader import load_unique_blocks


def analyze_files(
        dataset_path: Path,
        mod_text_path: Path,
        unique_lua_path: Path,
) -> tuple[BlockAnalysis, ...]:
    dataset = load_unique_dataset(dataset_path)
    mod_texts = load_mod_texts(mod_text_path)
    blocks = load_unique_blocks(unique_lua_path)

    unique_index = index_uniques_by_identity(dataset)

    return analyze_unique_blocks(
        blocks,
        unique_index,
        mod_texts,
    )