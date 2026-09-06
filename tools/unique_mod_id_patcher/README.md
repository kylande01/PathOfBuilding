# PoB unique mod-ID patcher

This is an isolated Python 3.10+ tool for auditing and patching mod IDs in
Path of Building 1 unique-item export files.

It provides:

- a standalone graphical interface built with Python's included
  `tkinter`/`ttk` toolkit;
- a command-line interface for scripted analysis and batch writing; and
- a tested backend shared by both interfaces.

## Inputs

- A genuine machine-readable `uniques.json`. Its mod IDs are authoritative.
- The repository's generated `src/Data/ModItemExclusive.lua`, used read-only
  to resolve existing and candidate IDs to their stat text.
- One contributor-selected `src/Export/Uniques/*.lua` file to analyze and,
  after confirmation, patch.

## Graphical interface

From `tools/unique_mod_id_patcher`, run:

```powershell
python -m unique_mod_id_patcher.gui
```

The interface follows the list-and-detail workflow used by Dat View:

- choose or confirm the three input paths;
- analyze the selected unique export;
- search and filter the result table;
- inspect original and proposed lines;
- select any subset of safe replacements; and
- confirm and apply the selected batch.

All high-confidence replacements are selected by default. Unresolved,
ambiguous, historical, already-current, and unmatched entries are visible but
cannot be selected for patching.

## Command-line interface

Analyze without changing the selected export:

```powershell
python -m unique_mod_id_patcher `
  --dataset ../../uniques.json `
  --mod-text ../../src/Data/ModItemExclusive.lua `
  --unique-lua ../../src/Export/Uniques/boots.lua
```

Apply every safe replacement in that selected file:

```powershell
python -m unique_mod_id_patcher `
  --dataset ../../uniques.json `
  --mod-text ../../src/Data/ModItemExclusive.lua `
  --unique-lua ../../src/Export/Uniques/boots.lua `
  --write
```

The CLI is read-only unless `--write` is supplied explicitly.

## Safety rules

The tool patches only exact, current-variant occurrences when:

1. one JSON unique matches the Lua block's name and current base type;
2. one authoritative mod ID has exactly the same resolved stat-text tuple; and
3. the existing line, mod-ID span, and replacement ID pass validation.

A selected batch is built and validated completely in memory. Duplicate line
targets abort the batch. File output is written to a temporary file in the
same directory, flushed, verified, given the original file's permission mode,
and atomically moved over the original.

Lua variant tags, value selectors, encoding, line endings, unrelated lines,
and the final newline are preserved. Re-running analysis after a successful
batch should report zero remaining replacements for the IDs just updated.

## Current limitations

- Only one unique export file is processed per run.
- Variants without an explicit label containing `Current` are handled
  conservatively rather than guessed.
- Roll-range differences, additions or removals, fuzzy matching, and generated
  data updates are not performed.
- Unmatched identities and unresolved or ambiguous mods require manual review.

## Tests

From `tools/unique_mod_id_patcher`, run:

```powershell
python -m unittest discover -s tests -v
```

The backend was developed incrementally with fixtures covering JSON loading,
Lua parsing, variant handling, matching, reporting, batch replacement,
line-ending preservation, atomic file writing, CLI behavior, and GUI result
selection.
