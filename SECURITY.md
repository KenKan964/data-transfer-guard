# Security / セキュリティ

No network, telemetry, credentials, updates or data transfer are used by the CLI.
This release uses synthetic fixtures only. Never attach real CSVs, raw IDs or
sensitive policy column names to public issues. Reports suppress cell values
and IDs by default; column names, record numbers and file hashes can still be
sensitive. `--show-keys` explicitly reveals IDs.

The repository is public and v0.1.0 is an experimental pre-release.
GitHub Private Vulnerability Reporting is a possible private channel; its
activation has **not been independently verified**. If “Report a vulnerability”
is available under Security, use it. Do not publish sensitive reports in
public issues, and do not assume any unlisted contact address is active.

The CLI is not a sandbox for hostile filesystem owners. Concurrent input
replacement, FIFO/device inputs, resource exhaustion and malicious same-user
processes are outside this MVP's assurance. Use ordinary, stable regular files
in a trusted local directory. SHA-256 identifies the bytes read, not a signed
attestation or proof of business correctness. Protect reports locally.

Supported code target: Python 3.11+. GitHub Actions passed all six
Ubuntu/Windows × Python 3.11/3.12/3.13 jobs on
[main run #3](https://github.com/KenKan964/data-transfer-guard/actions/runs/43458416344).
Check newer runs for later changes. No independent security audit is claimed.
