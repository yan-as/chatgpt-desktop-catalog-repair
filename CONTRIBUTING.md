# Contributing

Thank you for helping make local catalog repair safer.

Please keep every mutation narrowly scoped, backup-first, and covered by tests. Do not add heuristics that delete conversations based only on a title, a missing-candidate flag, or a failed network request. Schema support should be additive: new tables must be explicitly allow-listed and tested.

Before opening a pull request, run `python -m pytest` and `python -m ruff check .`.
