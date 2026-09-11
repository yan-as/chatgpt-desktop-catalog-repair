## Summary

Describe the behavior changed and why.

## Safety review

- [ ] The change keeps `inspect` read-only.
- [ ] Every new mutation has an explicit confirmation path and a SQLite backup.
- [ ] No deletion is inferred from a title or ambiguous network state.
- [ ] Tests cover the changed behavior using synthetic data only.

## Validation

- [ ] `python -m pytest`
- [ ] `python -m ruff check .`
