# Demo (draft)

A small Gradio app: type a sentence, see each value found, its confidence and, when the
parser cannot decide, every candidate.

```bash
pip install -e ".[demo]"
python demo/app.py        # http://localhost:7860
```

Launched once locally (the page answered on port 7860); not deployed anywhere. To put it on Hugging Face Spaces later: create a Gradio Space, copy
`demo/app.py` as `app.py`, and add a `requirements.txt` containing `kitna` (once a
development release is on PyPI) and `gradio`. Keep the pre-alpha notice at the top.
