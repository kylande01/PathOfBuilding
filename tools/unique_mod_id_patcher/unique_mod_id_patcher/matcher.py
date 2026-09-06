from collections.abc import Mapping

from .models import (
    BlockAnalysis,
    ModMatch,
    ModMatchStatus,
    ModOccurrence,
    UniqueBlock,
    UniqueDataset,
    UniqueItem,
)
from .unique_lua_loader import (
    applies_to_current_variant,
    find_current_base_types,
    find_mod_occurrences,
)


def index_uniques_by_identity(
        dataset: UniqueDataset,
) -> dict[tuple[str, str], tuple[UniqueItem, ...]]:
    grouped_uniques: dict[
        tuple[str, str],
        list[UniqueItem],
    ] = {}

    for unique in dataset.uniques:
        identity = (unique.name, unique.base_type)

        if identity not in grouped_uniques:
            grouped_uniques[identity] = []

        grouped_uniques[identity].append(unique)

    return {
        identity: tuple(uniques)
        for identity, uniques in grouped_uniques.items()
    }


def find_unique_candidates(
        block: UniqueBlock,
        unique_index: dict[
            tuple[str, str],
            tuple[UniqueItem, ...],
        ],
) -> tuple[UniqueItem, ...]:
    possible_base_types = {
        base_type
        for unique_name, base_type in unique_index
        if unique_name == block.name
    }

    current_base_types = find_current_base_types(
        block,
        possible_base_types,
    )

    candidates: list[UniqueItem] = []

    for base_type in current_base_types:
        identity = (block.name, base_type)
        candidates.extend(unique_index.get(identity, ()))

    return tuple(candidates)


def find_mod_id_candidates(
        occurrence: ModOccurrence,
        unique: UniqueItem,
        mod_texts: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    existing_text = mod_texts.get(occurrence.mod_id)

    if existing_text is None:
        return ()

    return tuple(
        candidate_mod.mod_id
        for candidate_mod in unique.mods
        if mod_texts.get(candidate_mod.mod_id) == existing_text
    )


def classify_mod_match(
        occurrence: ModOccurrence,
        candidate_ids: tuple[str, ...]
) -> ModMatch:
    if occurrence.mod_id in candidate_ids:
        status = ModMatchStatus.ALREADY_CURRENT
    elif not candidate_ids:
        status = ModMatchStatus.UNRESOLVED
    elif len(candidate_ids) == 1:
        status = ModMatchStatus.REPLACEMENT
    else:
        status = ModMatchStatus.AMBIGUOUS

    return ModMatch(
        occurrence=occurrence,
        status=status,
        candidate_ids=candidate_ids,
    )


def match_block_mods(
        block: UniqueBlock,
        unique: UniqueItem,
        mod_texts: Mapping[str, tuple[str, ...]],
) -> tuple[ModMatch, ...]:
    occurrences = find_mod_occurrences(
        block,
        known_mod_ids=mod_texts.keys(),
    )
    matches: list[ModMatch] = []

    for occurrence in occurrences:
        if not applies_to_current_variant(block, occurrence):
            continue

        candidate_ids = find_mod_id_candidates(
            occurrence,
            unique,
            mod_texts,
        )
        match = classify_mod_match(
            occurrence,
            candidate_ids,
        )
        matches.append(match)

    return tuple(matches)


def analyze_unique_block(
        block: UniqueBlock,
        unique_index: dict[
            tuple[str, str],
            tuple[UniqueItem, ...],
        ],
        mod_texts: Mapping[str, tuple[str, ...]],
) -> BlockAnalysis:
    unique_candidates = find_unique_candidates(
        block,
        unique_index,
    )

    if len(unique_candidates) == 1:
        mod_matches = match_block_mods(
            block,
            unique_candidates[0],
            mod_texts,
        )
    else:
        mod_matches = ()

    return BlockAnalysis(
        block=block,
        unique_candidates=unique_candidates,
        mod_matches=mod_matches,
    )


def analyze_unique_blocks(
        blocks: tuple[UniqueBlock, ...],
        unique_index: dict[
            tuple[str, str],
            tuple[UniqueItem, ...],
        ],
        mod_texts: Mapping[str, tuple[str, ...]],
) -> tuple[BlockAnalysis, ...]:
    return tuple(
        analyze_unique_block(
            block,
            unique_index,
            mod_texts,
        )
        for block in blocks
    )