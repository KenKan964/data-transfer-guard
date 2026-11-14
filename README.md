# Data Transfer Guard

**Check what changed between two CSV files — and detect edits outside the columns you explicitly allow.**

**v0.1.0 — Experimental · Python 3.11+ · Standard library only · CSV-only · MIT License**

**English** | [日本語](README_ja.md) · [v0.1.0 pre-release](https://github.com/KenKan964/data-transfer-guard/releases/tag/v0.1.0)

## Why use it?

A CSV update can look successful while silently changing the wrong field, removing a record, or duplicating an ID. For workflows where only certain columns should change, reviewing thousands of cells manually is difficult.

Data Transfer Guard is a **free, read-only command-line validator** for checking a **before** and **after** CSV against an explicit update policy.

It matches records by a chosen single ID column, checks which changes are permitted, and produces a JSON diagnostic report. **It never transfers, edits, repairs, or overwrites the input CSVs.**

> **Scope:** The tool verifies that two snapshots follow your declared *change rules*. It cannot tell whether a value entered in an allowed column is factually or commercially correct.

## What can it detect?

| Check | What it finds |
| --- | --- |
| Protected columns | Values changed outside the list of allowed update columns (`UNAUTHORIZED_CHANGE`) |
| Missing / added records | Removed or new rows when the policy forbids them |
| Duplicate or missing IDs | Ambiguous or invalid keys that prevent trustworthy matching |
| Schema differences | Header-set changes and missing required columns |
| Malformed CSV | Invalid quoting, ragged rows, duplicate headers, blank records, and unsupported encoding |
| Output safeguards | Existing or unsafe report paths are refused instead of overwritten |

**Comparison rules:** IDs and values are compared as exact strings. `001` and `1` are different, as are empty strings and `0`. Record order and column order may change; the set of headers must still match.

## Quick start

**Requirements:** Python 3.11 or newer. No external services or pip dependencies.

From the repository root, create a directory for the output reports.

**Linux / macOS:**

```sh
mkdir -p reports
python3 dtg.py verify --before examples/before.csv --after examples/after_ok.csv --policy examples/policy.json --out reports/ok.json
python3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
```

**Windows PowerShell:**

```powershell
New-Item -ItemType Directory -Force reports | Out-Null
py -3 dtg.py verify --before examples/before.csv --after examples/after_ok.csv --policy examples/policy.json --out reports/ok.json
py -3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
```

Use **new report file names** for each run; existing files are never overwritten. The second command deliberately returns exit code `1`: detecting the bad example is the expected outcome, not a malfunction. For each sample, the report is written to the specified JSON file.

## An example of a detected change

The included policy [`examples/policy.json`](examples/policy.json) permits changes to column **`状態` (status)** only. In the deliberately bad sample, column **`所属` (affiliation)** changes instead.

The committed [sample failure report](evidence/example_bad.json) includes these actual fields (excerpt):

```json
{
  "status": "FAIL",
  "exit_code": 1,
  "inspection_complete": true,
  "matched_rows": 2,
  "detection_count": 1,
  "counts_by_code": {
    "UNAUTHORIZED_CHANGE": 1
  },
  "violations": [
    {
      "code": "UNAUTHORIZED_CHANGE",
      "column": "所属",
      "key": null,
      "before_record": 2,
      "after_record": 2
    }
  ]
}
```

The normal sample returns `PASS`, exit code `0`, and zero detected violations; see [its recorded JSON](evidence/example_ok.json).

**Privacy by default:** the report does **not** include old or new cell values, and IDs are hidden as `null` unless `--show-keys` is explicitly selected. Column names, record positions, and file hashes can still reveal sensitive context.

## Configure the allowed changes

The example policy is:

```json
{
  "schema_version": "dtg-policy-v1",
  "key_column": "ID",
  "allowed_update_columns": ["状態"],
  "allow_added_rows": false,
  "allow_removed_rows": false
}
```

| Field | Meaning |
| --- | --- |
| `key_column` | Column containing a unique ID for each record |
| `allowed_update_columns` | Columns permitted to change; **the ID column cannot be included** |
| `allow_added_rows` | Whether new records may appear |
| `allow_removed_rows` | Whether records may disappear |
| `schema_version` | Policy contract version, currently `dtg-policy-v1` |

All five policy fields are required. Unknown or duplicate JSON keys, invalid field types, nonexistent columns, and invalid CSV structures are rejected rather than quietly ignored.

The tool performs no trimming, case folding, or Unicode normalization. Only UTF-8 (optionally with BOM) comma-separated CSV is supported.

## Exit codes and reporting

| Exit code | JSON status | Meaning |
| ---: | --- | --- |
| `0` | `PASS` | Comparison completed and the declared change rules were satisfied |
| `1` | `FAIL` | Comparison completed and one or more policy violations were found |
| `2` | `INVALID_INPUT` | Invalid input/policy, unreadable files, or output refusal/failure |

Reports include record counts, matches, violation types, input SHA-256 hashes, and runtime information. They never expose full cell values.

If writing the output is not safe or possible, an error JSON is sent to **stderr** and exit code `2` is returned. A partial or incomplete output must **not** be treated as successful evidence. The destination directory must already exist.

## Test and verification

The project includes **53 automated checks**: 49 CLI acceptance cases plus four additional checks. The acceptance cases include failures as well as successful comparisons; a correctly detected negative example counts as a successful **test**, even though the CLI reports `FAIL`.

**GitHub Actions:** Ubuntu and Windows × Python 3.11, 3.12, 3.13 — **all six jobs passed** on the published main-branch [run #3](https://github.com/KenKan964/data-transfer-guard/actions/runs/43458416344). For any newer changes, consult [the latest Actions runs](https://github.com/KenKan964/data-transfer-guard/actions). macOS has not been validated in this matrix.

Reproduce the checks locally:

```sh
python3 -m unittest discover -s tests -v
python3 benchmarks/compare.py comparison-001
```

Use `py -3` on Windows if needed. The comparison tool requires a new output directory. Its independent Python `csv` / `unittest` baseline demonstrates that similar checks can be implemented without DTG; no speed, human-effort, or commercial advantage is established.

## Safety and limitations

- **Read-only input:** this tool compares CSV snapshots; it performs **no updates or transfers**.
- No Excel, Google Sheets, database, cloud connector, network traffic, telemetry, or credentials.
- Strict exact-string matching: no composite IDs, fuzzy company-name matching, normalization, or verification of the *correctness* of permitted new values.
- Files are read into memory. Very large inputs, streaming, concurrent writers, special devices, and hostile filesystem changes are outside the intended scope.
- The displayed record positions are CSV record ordinals, **not necessarily physical line numbers** when fields contain line breaks.
- Treat reports as potentially sensitive even with IDs suppressed; protect them and avoid attaching real records to public issues.

## Documentation

- [日本語 README](README_ja.md)
- [Technical specification](TECHNICAL_SPEC.md)
- [Security considerations](SECURITY.md)
- [Recorded sample violation](evidence/example_bad.json)
- [Comparison evidence](evidence/comparison_final/summary.json)
- [Verification report](REPORT_ja.md)
- [Change history](CHANGELOG.md)
- [MIT License](LICENSE)

**License:** MIT · Copyright © 2026 KenKan964.
