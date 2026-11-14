# Demo (draft)

A small Gradio app: type a sentence, see each value found, its confidence and, when the
parser cannot decide, every candidate.

```bash
pip install -e ".[demo]"
python demo/app.py        # then open http://localhost:7860
```

The app listens on `127.0.0.1` by default. To reach it from another machine or inside a
container, set `HOST=0.0.0.0` (and still browse to the machine's real address, not `0.0.0.0`).

Launched once locally (the page answered on port 7860); not deployed anywhere. To put it on Hugging Face Spaces later: create a Gradio Space, copy
`demo/app.py` as `app.py`, and add a `requirements.txt` containing `kitna` (once a
development release is on PyPI) and `gradio`. Keep the pre-alpha notice at the top.
