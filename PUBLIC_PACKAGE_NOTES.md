# Public candidate packaging notes

This is a GitHub-browser-friendly distribution candidate derived from the full DTG-DEV-001 submission.

- Runtime code (`dtg.py`, `benchmarks/*.py`) and test code (`tests/*.py`, `tests/cases.json`) are **byte-for-byte unchanged** from the source submission.
- All 49 individual acceptance `before.csv`, `after.csv`, `policy.json`, `result.json` records have been condensed to `evidence/acceptance_summary.json` for publication. They remain reproducible by running the test suite.
- The 1,560-sample raw benchmark log is omitted; the comparison summary is retained. The original developer archive retains all original evidence.
- Documentation updated to describe the condensed evidence. MIT copyright line is set to `KenKan964` per publisher preference; publisher must confirm publication rights.
- No production data are included. The source submission was verified on Linux Python 3.13.5; Windows, Python 3.11 and GitHub Actions still require verification.
- This candidate has NOT been published to GitHub.
