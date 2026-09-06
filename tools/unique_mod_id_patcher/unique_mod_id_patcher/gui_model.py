from dataclasses import dataclass

from .models import BlockAnalysis, ModMatch, ModMatchStatus


ALL_RESULTS = "All results"
IDENTITY_ISSUES = "Identity issues"
UNMATCHED_UNIQUE = "Unmatched unique"
AMBIGUOUS_UNIQUE = "Ambiguous unique"
NO_CLASSIFIED_MODS = "No classified mods"

STATUS_LABELS = {
    ModMatchStatus.ALREADY_CURRENT: "Already current",
    ModMatchStatus.REPLACEMENT: "Replacement",
    ModMatchStatus.UNRESOLVED: "Unresolved",
    ModMatchStatus.AMBIGUOUS: "Ambiguous",
}


@dataclass(frozen=True)
class ResultRow:
    key: str
    status: str
    block_name: str
    base_type: str
    line_number: int | None
    existing_mod_id: str
    candidate_ids: tuple[str, ...]
    raw_line: str
    match: ModMatch | None

    @property
    def is_patchable(self) -> bool:
        return (
            self.match is not None
            and self.match.status is ModMatchStatus.REPLACEMENT
            and len(self.match.candidate_ids) == 1
        )

    @property
    def proposed_mod_id(self) -> str:
        if len(self.candidate_ids) == 1:
            return self.candidate_ids[0]
        return ", ".join(self.candidate_ids)


def build_result_rows(
    analyses: tuple[BlockAnalysis, ...],
) -> tuple[ResultRow, ...]:
    rows: list[ResultRow] = []

    for analysis_index, analysis in enumerate(analyses):
        candidate_count = len(analysis.unique_candidates)

        if candidate_count != 1:
            if candidate_count == 0:
                status = UNMATCHED_UNIQUE
                base_type = ""
            else:
                status = AMBIGUOUS_UNIQUE
                base_type = ", ".join(
                    candidate.base_type
                    for candidate in analysis.unique_candidates
                )

            rows.append(
                ResultRow(
                    key=f"identity:{analysis_index}",
                    status=status,
                    block_name=analysis.block.name,
                    base_type=base_type,
                    line_number=analysis.block.start_line,
                    existing_mod_id="",
                    candidate_ids=(),
                    raw_line=analysis.block.name,
                    match=None,
                )
            )
            continue

        unique = analysis.unique_candidates[0]

        if not analysis.mod_matches:
            rows.append(
                ResultRow(
                    key=f"empty:{analysis_index}",
                    status=NO_CLASSIFIED_MODS,
                    block_name=analysis.block.name,
                    base_type=unique.base_type,
                    line_number=analysis.block.start_line,
                    existing_mod_id="",
                    candidate_ids=(),
                    raw_line=analysis.block.name,
                    match=None,
                )
            )
            continue

        for match_index, match in enumerate(analysis.mod_matches):
            rows.append(
                ResultRow(
                    key=f"mod:{analysis_index}:{match_index}",
                    status=STATUS_LABELS[match.status],
                    block_name=analysis.block.name,
                    base_type=unique.base_type,
                    line_number=match.occurrence.line_number,
                    existing_mod_id=match.occurrence.mod_id,
                    candidate_ids=match.candidate_ids,
                    raw_line=match.occurrence.raw_line,
                    match=match,
                )
            )

    return tuple(rows)


def collect_selected_replacements(
    rows: tuple[ResultRow, ...],
    selected_keys: set[str],
) -> tuple[ModMatch, ...]:
    return tuple(
        row.match
        for row in rows
        if (
            row.key in selected_keys
            and row.is_patchable
            and row.match is not None
        )
    )
