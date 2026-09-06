from .models import BlockAnalysis, ModMatchStatus


def format_analysis_report(
        analyses: tuple[BlockAnalysis, ...],
) -> str:
    exact_identity_count = sum(
        1
        for analysis in analyses
        if len(analysis.unique_candidates) ==1
    )
    unmatched_identity_count = sum(
        1
        for analysis in analyses
        if not analysis.unique_candidates
    )
    ambiguous_identity_count = sum(
        1
        for analysis in analyses
        if len(analysis.unique_candidates) > 1
    )

    mod_matches = [
        match
        for analysis in analyses
        for match in analysis.mod_matches
    ]

    already_current_count = sum(
        1
        for match in mod_matches
        if match.status is ModMatchStatus.ALREADY_CURRENT
    )
    replacement_count = sum(
        1
        for match in mod_matches
        if match.status is ModMatchStatus.REPLACEMENT
    )
    unresolved_count = sum(
        1
        for match in mod_matches
        if match.status is ModMatchStatus.UNRESOLVED
    )
    ambiguous_mod_count = sum(
        1
        for match in mod_matches
        if match.status is ModMatchStatus.AMBIGUOUS
    )

    lines = [
        f"Blocks analyzed: {len(analyses)}",
        f"Exact unique identities: {exact_identity_count}",
        f"Unmatched unique identities: {unmatched_identity_count}",
        f"Ambiguous unique identities: {ambiguous_identity_count}",
        f"Already-current mods: {already_current_count}",
        f"Replacement candidates: {replacement_count}",
        f"Unresolved mods: {unresolved_count}",
        f"Ambiguous mods: {ambiguous_mod_count}",
    ]

    for analysis in analyses:
        for match in analysis.mod_matches:
            if (
                match.status is ModMatchStatus.REPLACEMENT
                and len(match.candidate_ids) == 1
            ):
                lines.append(
                    "Replacement line "
                    f"{match.occurrence.line_number}: "
                    f"{match.occurrence.mod_id} "
                    f"-> {match.candidate_ids[0]}"
                )
            elif match.status is ModMatchStatus.UNRESOLVED:
                lines.append(
                    "Unresolved line "
                    f"{match.occurrence.line_number}: "
                    f"{match.occurrence.mod_id}"
                )
            elif match.status is ModMatchStatus.AMBIGUOUS:
                candidate_text = ", ".join(match.candidate_ids)
                lines.append(
                    "Ambiguous line "
                    f"{match.occurrence.line_number}: "
                    f"{match.occurrence.mod_id} "
                    f"-> {candidate_text}"
                )

    return "\n".join(lines)