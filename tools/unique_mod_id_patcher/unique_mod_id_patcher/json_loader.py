import json
from pathlib import Path

from .models import ModStat, UniqueDataset, UniqueItem, UniqueMod

def load_unique_dataset(path: Path) -> UniqueDataset:
    with path.open("r", encoding="utf-8") as input_file:
        raw_dataset = json.load(input_file)

    raw_uniques = raw_dataset.get("uniques")

    if not isinstance(raw_uniques, list):
        raise ValueError("Expected a top-level 'uniques' list")

    uniques: list[UniqueItem] = []

    for raw_unique in raw_uniques:
        mods: list[UniqueMod] = []

        for raw_mod in raw_unique["mods"]:
            stats: list[ModStat] = []

            for raw_stat in raw_mod["stats"]:
                stat = ModStat(
                    stat_id=raw_stat["statId"],
                    minimum=raw_stat["min"],
                    maximum=raw_stat["max"],
                )
                stats.append(stat)

            mod = UniqueMod(
                mod_group=raw_mod["modGroup"],
                mod_id=raw_mod["modId"],
                stats=tuple(stats),
            )
            mods.append(mod)

        unique = UniqueItem(
            name=raw_unique["name"],
            base_type=raw_unique["baseType"],
            vestigial_observed=raw_unique["vestigialObserved"],
            mods=tuple(mods),
        )
        uniques.append(unique)

    return UniqueDataset(league_name=raw_dataset["leagueName"], uniques=tuple(uniques),
)