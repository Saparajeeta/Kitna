# Kitna demo

Paste a message; see every amount, date and time highlighted with a plain-language reading, choose
when a phrase has two meanings, and see the tool call an agent would send. Pre-alpha: the rules are
AI-drafted, not reviewed by native speakers, and no accuracy has been measured.

## Run it locally

```bash
pip install -e ".[demo,compare]"
python demo/app.py        # then open http://localhost:7860
```

- Reviewer mode (for friends who speak Hindi): http://localhost:7860/review
- `compare` is optional. Without it the comparison tab says the libraries are not installed.
- The app listens on `127.0.0.1`. For another machine or a container set `HOST=0.0.0.0`
  (and browse to the machine's real address). `PORT` changes the port.

## What is on the page

| Where | What |
|---|---|
| Read | Message with values highlighted, one question per ambiguous phrase, a card per value with a confidence label and a "Why?" (English or Hindi), raw fields under "Details" |
| Read, lower half | "Make it an action": confirmation sentence, Confirm (locked while anything is ambiguous), Edit, the tool call with a copy button. Preview only; nothing runs |
| Read, bottom | JSON for developers, share link, "Was this right?" feedback, light/dark switch |
| Compare | The same message through number-parser and dateparser, run live, with their versions |
| Speak | Only with `KITNA_VOICE=1`; see below |
| About | What has and has not been measured, with links to the files |
| `/review` | One draft case per card; ok / wrong / unnatural; progress bar; CSV download |

Keyboard: Ctrl+Enter (or Cmd+Enter, or Shift+Enter) reads the message.

## Privacy

- Nothing typed is written to disk or logged by the app. Gradio analytics are off, fonts are system
  fonts, and the page loaded no third-party resource in our headless-browser check.
- Feedback is built in the browser as a JSON line or a prefilled GitHub issue link. It leaves the
  device only if the visitor presses "open issue" or sends the file.
- Reviewer answers live in the reviewer's own browser storage until they download the CSV.
- A shared link carries the message text in the URL. Do not share links to private messages.

## Reviewer mode: how answers come back

1. The reviewer opens `/review`, answers as many cards as they like (answers survive a reload), and
   presses "Get my CSV".
2. They send you `kitna_review.csv` (chat, email).
3. The file has the same columns and row order as `docs/review/phase1_cases_review.csv`, so it can be
   opened in a spreadsheet or compared with `git diff --no-index`.

Cases whose rule is still undecided are shown first.

## Voice (stretch, off by default)

```bash
pip install -e ".[demo,voice]"
KITNA_VOICE=1 python demo/app.py          # Windows cmd: set KITNA_VOICE=1 && python demo/app.py
```

Uses a pretrained Whisper model through `faster-whisper` on the CPU (`KITNA_VOICE_MODEL`, default
`small`); nothing is trained. The model file is downloaded once from Hugging Face, then audio stays on
the machine running the app. The transcript is shown in an editable box before Kitna reads it,
because transcripts can be wrong. **No speech accuracy has been measured, and this path has not been
run end to end by the author** (the build sandbox could not download the model); only the wiring is
tested, with a stand-in transcriber.

On a hosted Space "locally" means the Space's server, not the visitor's device. Say so if you enable it there.

## Put it on Hugging Face Spaces

Not deployed yet. Exact steps:

1. Create the Space: https://huggingface.co/new-space → name `kitna`, SDK **Gradio**, hardware
   **CPU basic**, visibility as you prefer.
2. Build the folder (uploads nothing):
   ```bash
   python scripts/build_space.py          # writes space_build/
   ```
3. Push it:
   ```bash
   pip install -U huggingface_hub
   huggingface-cli login                  # a token with "write" access
   huggingface-cli upload <your-username>/kitna space_build . --repo-type space
   ```
4. Wait for "Running", then open `https://huggingface.co/spaces/<your-username>/kitna`.
   Reviewer page: the direct app address plus `/review`
   (`https://<your-username>-kitna.hf.space/review`).
5. Check before sharing: the pre-alpha banner is visible; the Payment request example shows the
   AM/PM question; Confirm is locked until you choose; `/review` shows "Case 1 of …".

Notes:
- `requirements.txt` installs Kitna from the `main` branch, so merge the pull request first (or
  replace `@main` with a commit hash).
- `sdk_version` in `demo/space/README.md` is the Gradio version the demo was tested with.
- To update the Space, rerun steps 2 and 3.
