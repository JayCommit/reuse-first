## Summary

## Checks

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/pattern_index.py --help`
- [ ] formatter query returns `legacy.py` and `presentation.py`
- [ ] missing query returns JSON `files: []` and exits 0
- [ ] `git diff --check`

Note the Python version, any skipped tests, and anything you did not run.
Do not claim a without-skill baseline, reduced duplication, or a green GitHub
Actions run unless you actually observed it.

## Notes

Remove secrets and private paths. Keep changes on the standard library unless
the maintainers have agreed otherwise.
