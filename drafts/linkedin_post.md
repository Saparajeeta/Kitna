# LinkedIn post (draft, AI-written, not published)

<!-- Fill every [bracket] from a file in results/ and list it in docs/claims_checklist.md. Delete lines you cannot back. -->

"Ramesh ko kal dhai lakh bhej dena."

A person reads that instantly. For software it holds three small traps: "dhai lakh" is a
fraction idiom on an Indian scale word, "kal" means both yesterday and tomorrow, and it is
Hindi typed in English letters.

I built Kitna to look at this properly. Two parts:

1. A small Python library that turns Hinglish and Devanagari amounts, times and dates into
   exact values. When something is unclear ("5 baje", a bare "kal") it returns every
   candidate instead of guessing.
2. A tool-calling benchmark: [N scenarios] everyday requests, each in Devanagari, Roman
   Hinglish and English. The Hinglish lines were written by [N writers] native speakers and
   labelled independently by [N annotators] others (agreement: [kappa]).

What I found: [one sentence, only if a run in results/bench/ supports it. Otherwise delete
this paragraph and say the benchmark is open for anyone to run.]

What it is not: the parser is rule-based and pre-alpha, the benchmark is small, and the
English and Devanagari lines are AI-drafted. The limits are written down in the repo.

Code (Apache licence) and data (Creative Commons Attribution): [link]

If you speak Hindi and want to help, the open questions page lists the decisions where I
need a native speaker's ear: [link]
