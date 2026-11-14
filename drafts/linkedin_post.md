# LinkedIn post (draft, AI-written, not published)

<!-- Every [TBD ...] must be filled from a file in results/ and listed in docs/claims_checklist.md
     (section "Claims in the post and the demo script"). Delete any line you cannot back.
     Do not write "first" or "only". Do not post before a native speaker has reviewed the rules. -->

"Ramesh ko kal 5 baje dhai lakh rupaye bhej dena."

A person reads that instantly. Software has to get three things right: "dhai lakh" is a fraction
idiom on an Indian scale word, "kal" is both yesterday and tomorrow, and "5 baje" does not say
morning or evening. A slip here is a payment with a wrong zero or a reminder at the wrong hour.

I built Kitna, a small open-source Python library for exactly this. It reads Hinglish and
Devanagari amounts, dates and times into exact values. When the words do not decide, it does not
guess: it returns every reading and the app asks the person.

What you can try in the demo ([TBD link to the hosted demo]):

- Paste a message and see each value highlighted with its meaning in plain words.
- Pick between readings when a phrase is ambiguous, with the reason shown.
- See why each value was read that way, in English or Hindi.
- See the tool call an agent would send, as a confirmation you can check before anything runs.
- Run the same text through two existing libraries, live, and compare.

For developers: `pip install`, one function call, or a local HTTP service. There is also a helper
that checks an LLM's tool call against what the user actually said.

What I measured: [TBD one sentence, copied from a file in results/ once the held-out set and a
real benchmark run exist. If there is none, delete this paragraph.]

What it is not: it is pre-alpha and rule-based. The rules were drafted with an AI assistant and
reviewed by [TBD number] native Hindi speakers so far. There is no accuracy figure until a
held-out set written by native speakers exists. The limits are written down in the repository.

If you speak Hindi, you can help in a few minutes: the demo has a reviewer page where you mark
draft examples ok, wrong or unnatural on your phone. [TBD link]

Code (Apache licence): [TBD link]
