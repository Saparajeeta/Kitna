# Demo script, about one minute (draft, AI-written, not recorded)

<!-- Timings are a guide. Every [TBD ...] must be filled from a file in results/ and listed in
     docs/claims_checklist.md. Say nothing about accuracy or about how often models fail unless a
     results file backs it. Record against the gallery examples so the screen matches the words. -->

Setup before recording: open the demo, light theme, phone-width or a narrow window. Leave the
"now" fields as the gallery sets them.

| Time | On screen | Say |
|---|---|---|
| Opening | The headline and the pre-alpha banner | "People in India type money and time like this: dhai lakh, parso, saade teen baje. Kitna is a small open-source library that reads them exactly, or tells you it's unsure. It is pre-alpha and not yet validated by native speakers." |
| Ambiguity | Tap **Payment request**. The message lights up; the question appears | "Dhai lakh rupaye: two and a half lakh, exact. But kal 5 baje has no morning or evening word. Kitna does not guess. It asks." |
| Choice | Tap the PM option. The card changes to "Chosen by you"; Confirm unlocks | "I pick 5 PM. Only now can the action be confirmed. This is a preview: nothing is sent." |
| Context | Tap **Reminder**. Open "Why?" | "Here it is 10 in the morning and the verb is future, so 2 o'clock can only be the afternoon. The card says which rule decided, and that this rule still waits for a native speaker's review." |
| Comparison | Open **Compare**, press the button | "The same sentence through two general-purpose libraries, run live right now, with their versions. These are outputs for this one sentence, not a score." |
| Developers | Scroll to the tool call; copy it | "For developers: this is the tool call an agent would send. One function checks a model's call against what the user actually said." |
| Close | The reviewer page on a phone | "[TBD number] Hindi speakers have reviewed the rules so far. If you speak Hindi, this page lets you check examples in a few minutes. Link below." |

Lines to leave out unless a results file backs them:

- Any accuracy figure for Kitna ([TBD], needs the held-out set).
- Any statement that a named model gets these wrong, or how often ([TBD], needs a real benchmark run).
- Any speed figure ([TBD], nothing has been timed on a hosted demo).
