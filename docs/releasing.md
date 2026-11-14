# Releasing

Nothing has been published. This page is the procedure and the checklist.

## Version policy

- Until **both** of these are true, only development releases (`0.1.0.devN`) are published:
    1. native speakers have reviewed the parser cases and the open questions
       ([list](open_questions.md)) have answers recorded in `policy.tsv`;
    2. a held-out set exists and is frozen ([protocol](heldout_protocol.md)), and its
       result is in `results/heldout/`.
- `0.1.0` is tagged only after that. Its release notes state the held-out result.
- A change that alters parser output for existing input is a behaviour change: it gets a
  changelog entry and, after `0.1.0`, a minor version bump. A change to the JSON output's
  meaning bumps `schema_version`.
- The benchmark data is versioned separately (`dev_v1`, `v2`...). A frozen file is never
  edited.

## What has been verified, and how

Checked in this repository's sandbox, which has Python 3.11 only and no Docker:

| Step from the workflows | Verified locally? |
|---|---|
| `ruff check .`, `mypy`, case validator, policy-docs check, `pytest` | yes, on Python 3.11 |
| Benchmark job: item validator, seed/drafts up to date, tests, mock run, claims check | yes, on Python 3.11 |
| `mkdocs build --strict` | yes |
| `python -m build`, `twine check`, install the wheel in a clean venv, run `kitna` | yes |
| Release job: tag-equals-version test, tests against the built wheel | yes, by running the same commands with `GITHUB_REF_NAME=v0.1.0.dev0` |
| Workflow files are valid (schema check with `check-jsonschema`) | yes |

**Not verified** (cannot be, here):

- The release workflow has never run on GitHub. `act` needs Docker, which is not available.
- The CI workflow first ran on GitHub when the benchmark-tooling pull request was merged.
  Python 3.11 to 3.14, the benchmark job, the docs job and the package job passed. Python
  3.10 failed at the type check (a two-argument `joinpath` that 3.10's type stubs reject).
  That is fixed, and `mypy` now always checks against 3.10; the fix is confirmed only once
  CI is green on the pull request that carries it.
- OIDC trusted publishing to PyPI (needs the pending publisher and a real tag).
- Dependabot and the release-notes categories (GitHub-side features).
- `pre-commit run --all-files`: hook repositories could not be fetched in the sandbox
  network; the local hooks' commands were run by hand.

## Checklist for the first development release (project owner)

1. Open a pull request from the working branch and wait for CI. Fix anything red: this is
   the first real run of the matrix.
2. On pypi.org: *Your account → Publishing → Add a new pending publisher* (GitHub):
    - PyPI project name: `kitna`
    - Owner: `Saparajeeta`
    - Repository name: `Kitna`
    - Workflow name: `release.yml`
    - Environment name: `pypi`
3. On GitHub: *Settings → Environments → New environment* named `pypi`. Optional but
   sensible: require your approval for deployments to it.
4. Merge the pull request into `main`.
5. Check that `src/kitna/__init__.py` says `__version__ = "0.1.0.dev0"`.
6. Tag and push:

    ```bash
    git checkout main && git pull
    git tag v0.1.0.dev0
    git push origin v0.1.0.dev0
    ```

7. Watch the *Release* workflow. The build job fails if the tag and the package version
   differ. Approve the `pypi` deployment if you required approval.
8. Verify from a clean environment:

    ```bash
    python -m venv /tmp/kitna-check && . /tmp/kitna-check/bin/activate
    pip install --pre kitna==0.1.0.dev0
    kitna parse "dhai lakh"          # expect: number  250000
    python -c "import kitna; print(kitna.__version__)"
    ```

9. Create the GitHub release from the tag using `.github/RELEASE_NOTES_TEMPLATE.md`. Mark it
   as a pre-release.
10. For the next development release, bump `__version__` to `0.1.0.dev1` first.

A version number can never be reused on PyPI, even after deleting a release.

## Local tooling

- `pip install pre-commit && pre-commit install` runs lint, type checks and the data checks
  before each commit (`.pre-commit-config.yaml`).
- Dependabot opens monthly update pull requests for GitHub Actions and Python tooling.
- Commit messages and pull-request titles follow Conventional Commits (`feat:`, `fix:`,
  `data:`, `docs:`, `test:`, `ci:`, `build:`; `!` for behaviour changes). Release-note
  sections follow those types.
