# Security policy

## Supported versions

Kitna is pre-alpha. Only the latest published development release and the `main`
branch receive fixes.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting:
**Security → Report a vulnerability** on
<https://github.com/Saparajeeta/Kitna/security/advisories/new>.
(Owner action: private vulnerability reporting must be enabled in the
repository settings for this link to work. `[TBD: confirm enabled]`)

Include the input text, the call you made and the version (`kitna --version`).

## What counts

Kitna's core has no runtime dependencies, makes no network calls and executes
no input. Realistic issues are: inputs that make parsing very slow or exhaust
memory, a packaged data table that could be made to load code, and problems in
the release workflow. A wrong parse is a bug, not a vulnerability; please file
it as a normal issue.

The benchmark harness (when it exists) will call model APIs with keys from
environment variables. Never commit keys; raw model outputs are saved to
`results/` and should be checked for secrets before committing.
