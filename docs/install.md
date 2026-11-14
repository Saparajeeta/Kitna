# Install

Kitna needs Python 3.10 or newer and has no runtime dependencies.

## From PyPI

Not published yet. When a development release exists it will be installed with:

```bash
pip install --pre kitna
```

`--pre` is required because only development releases (`0.1.0.devN`) will be
published until native-speaker review and the held-out set are done.

## From a checkout

```bash
git clone https://github.com/Saparajeeta/Kitna
cd Kitna
pip install -e ".[dev]"     # library + test tools
pytest
```

Building these docs: `pip install -e ".[docs]"` then `mkdocs serve`.

## Check it works

```console
$ kitna parse "dhai lakh"
number	250000	confidence=1.0	'dhai lakh'
```
