# Security / セキュリティ

No network, telemetry, credentials, updates or data transfer are used by the CLI.
This release uses synthetic fixtures only. Never attach real CSVs, raw IDs or
sensitive policy column names to public issues. Reports suppress cell values
and IDs by default; column names, record numbers and file hashes can still be
sensitive. `--show-keys` explicitly reveals IDs.

Before public release the publisher must choose a security contact or enable
GitHub private vulnerability reporting. If enabled, use that private channel.
Do not publish sensitive reports when no private channel is available.

The CLI is not a sandbox for hostile filesystem owners. Concurrent input
replacement, FIFO/device inputs, resource exhaustion and malicious same-user
processes are outside this MVP's assurance. Use ordinary, stable regular files
in a trusted local directory. SHA-256 identifies the bytes read, not a signed
attestation or proof of business correctness. Protect reports locally.

Initial supported code target: Python 3.11+. Actual tested versions are in
REPORT_ja.md. GitHub CI is configured, not yet run. No security audit is claimed.
