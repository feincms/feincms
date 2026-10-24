# Agent notes

## Tests

- Quick run: `tox -e py313-dj52` (Django's test runner via
  `tests/manage.py test testapp`; there's no local virtualenv).
- Full matrix: `tox` (environments are listed in `tox.ini`, e.g.
  `tox -e py312-dj61`). CI (`.github/workflows/tests.yml`) runs every
  `py<version>-*` environment for each Python version in its matrix, so keep
  the CI matrix, the tox envlist and the classifiers in `setup.cfg` in sync.
- Browser tests: `tox -e e2e` (Playwright, tests marked with `e2e`; runs in
  `.github/workflows/e2e-tests.yml`).

## Conventions

- Run the hooks with `prek` (not `pre-commit`), e.g. `prek run --all-files`.
- Add user-facing changes to the "Next version" section of `CHANGELOG.rst`.

## Commits

- Commit feature by feature: one commit per fix or feature, each including
  its tests and changelog entry.
- No attribution lines (no `Co-Authored-By` etc.).
- Keep commit messages short and don't repeat what the diff or changelog
  already says; a concise subject line is usually enough.

## Releases

- Pushing a tag publishes the release to PyPI
  (`.github/workflows/publish.yml`, trusted publishing via the `release`
  environment).
