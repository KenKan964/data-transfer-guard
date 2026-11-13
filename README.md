# Data Transfer Guard

[日本語](README_ja.md) · CSV-only · Python 3.11+ · standard library only

Read-only verification of a CSV update: match rows by a single string ID,
permit changes only in declared columns, and report unexpected changes or
invalid input. This **does not transfer, edit or repair data**. Independent of
SQLite Fault Lab. Release candidate 0.1.0; not published to GitHub.

## Quick start (Linux/macOS)

No installation or pip packages required. From this extracted directory:

```bash
mkdir -p reports
python3 dtg.py verify --before examples/before.csv --after examples/after_ok.csv --policy examples/policy.json --out reports/ok.json
python3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
```

First command: exit **0**, JSON `status=PASS`. Second command: exit **1**,
`status=FAIL`, `UNAUTHORIZED_CHANGE` on column `所属`, key suppressed.
`evidence/example_bad.json` contains the complete synthetic example. The bad
example must be detected; its FAIL status is a successful tool demonstration.
The reports directory must exist; output filenames must be new. Re-running
with the same output filename is rejected, not overwritten.

## Windows PowerShell

```powershell
New-Item -ItemType Directory -Force reports | Out-Null
py -3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
$LASTEXITCODE # expected: 1
py -3 -m unittest discover -s tests -v
```

Use a Python 3.11+ interpreter. On Linux/macOS run tests with
`python3 -m unittest discover -s tests -v`.

## Policy and exact comparison

```json
{"schema_version":"dtg-policy-v1","key_column":"ID","allowed_update_columns":["状態"],"allow_added_rows":false,"allow_removed_rows":false}
```

All five fields are mandatory. Unknown/duplicate JSON fields, unknown columns,
duplicate allowed columns, allowing the ID column, non-boolean row flags and
unsupported versions are rejected. Set either row flag to true only if those
row changes are intentionally permitted; default examples forbid both.

IDs and cell values are exact strings. `001` differs from `1`, empty differs
from `0`, and spaces / embedded newlines are preserved. Blank or whitespace-only
IDs/headers are invalid. Other nonempty strings are never trimmed or normalized.
Row and header order may change; header sets must match. Missing required key
or allowed columns are INVALID_INPUT; other schema changes are FAIL.

UTF-8 or UTF-8 BOM only; comma delimiter, double quotes, doubled quote escaping.
LF/CRLF/CR record separators are accepted. Quotes in bare fields, trailing junk
after a quoted field, unclosed quotes, NULs, duplicate headers and ragged rows
are rejected. Blank records are invalid; header-only files are valid.

## Reports, privacy and exit codes

|Exit|JSON status|Meaning|
|---:|---|---|
|0|PASS|Inspection completed; policy satisfied|
|1|FAIL|Inspection completed; update-rule violation|
|2|INVALID_INPUT|Invalid policy/CSV, unreadable input, invalid CLI or output refusal|

Reports include row/match counts, violations, classification counts, SHA-256 of
bytes read and environment information. **Cell values are never included**.
Keys are `null` by default; record ordinals identify locations (not physical
line numbers when quoted fields contain newlines). `--show-keys` explicitly
reveals raw IDs: avoid for personal data. Column names and file hashes may also
be sensitive. If output is unsafe/unavailable, JSON is written to **stderr**
instead; the existing destination is preserved. Unknown counts/hashes are null.

Input files are opened only for reading. Output uses exclusive creation,
refusing an input path, existing report, symlink or existing hardlink alias.
No networking, credentials, telemetry or third-party runtime dependencies.
Use stable ordinary local files; concurrent writers are outside this MVP.

## Reproduce evidence and comparison

```bash
DTG_EVIDENCE_DIR=reports/acceptance python3 -m unittest discover -s tests -v
python3 benchmarks/compare.py reports/comparison
```

PowerShell: set `$env:DTG_EVIDENCE_DIR='reports/acceptance'` then run tests.
The comparison directory must be new. See [REPORT_ja.md](REPORT_ja.md) and
[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md). Fixtures and expected results are saved
in `tests/cases.json`: 49 CLI cases cover all DTG-T01–T16, plus four additional
checks. Each CLI test checks unchanged input hashes. Existing-output refusals
use stderr JSON; missing files remain missing.

Executed: Linux Python **3.12.14 and 3.13.5**, 53/53 each. Python 3.11,
Windows and macOS are **not locally verified**. GitHub Actions config targets
Ubuntu/Windows × 3.11/3.12/3.13 but has **not run**; configuration is not evidence.

## Value and limits

This packages repeatable policy checks, strict input validation, private-by-default
JSON evidence and output safeguards. An independent `csv` + `unittest` reference
can implement the same core rules; the policy mechanism is not unique to DTG.
The supplied core comparison is intentionally limited and does not equate
baseline report functionality with DTG. No human effort savings or commercial
demand have been measured. No speed advantage is claimed.

All files are read into memory. No streaming, normalization, composite keys,
Excel/Sheets connections, correction, expected-value verification of allowed
changes or business correctness guarantee. The standard CSV field size limit
applies. A PASS says only that these two snapshots obey the declared policy.

## Release and license

MIT candidate: [LICENSE](LICENSE); publisher must approve licensing/attribution
before release. See [SECURITY.md](SECURITY.md) and [CHANGELOG.md](CHANGELOG.md).
Review department acceptance, untested environments and security contact before
creating the independent `data-transfer-guard` repository. No GitHub publication
has been performed. No SQLite Fault Lab code is imported or modified.

## Consolidated public evidence

This release candidate consolidates 49 acceptance case records into `evidence/acceptance_summary.json`, avoiding repeated fixture CSVs. Original per-case files remain only in the development submission archive. All fixture bytes and assertions are reproducible from `tests/cases.json` and the test runner.
