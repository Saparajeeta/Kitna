<!-- Copy into the GitHub release body. Delete sections that are empty. Every number needs a link to results/. -->
# kitna vX.Y.Z

**Status of this release:** development release / pre-alpha. <!-- 0.1.0 only after native-speaker review + frozen held-out set -->

## What the numbers are
<!-- Keep this paragraph until a held-out result exists. -->
No accuracy figure. The parser agrees with its own AI-drafted cases
([results file](LINK)); that is a self-consistency check, not accuracy.

## Behaviour changes (output differs from the previous release)
- `fix!:` / `feat!:` ...  (policy row or table changed: `...`; who answered the open question: ...)

## Added
- `feat:` ...

## Spellings and policy (data only)
- `data:` ...

## Fixed
- `fix:` ...

## Result schema
`schema_version`: 1 (unchanged) <!-- or: bumped to N because ... -->

## Known limitations
See docs/limitations.md. New in this release: ...

## Verification
- CI run: LINK
- Clean install checked: `pip install --pre kitna==X.Y.Z && kitna parse "dhai lakh"` -> `250000`
