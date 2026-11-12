# Taxonomy and canonical forms (DRAFT for review)

Status: **draft, written by an AI agent, not yet reviewed by a native speaker.**
Every rule below is a proposal. Rules where I am least sure are collected under
[Open questions](#open-questions) with the case IDs they affect.

Cases live in `tests/golden/draft_cases.jsonl` (292 cases). A spreadsheet copy
for marking up is at `docs/review/phase1_cases_review.csv`.

## 1. Kinds and canonical values

| kind | canonical `value` | example |
|---|---|---|
| `number` | integer, or exact decimal (shown as a string in JSON: `"3.25"`) | `dhai lakh` -> 250000 |
| `digits` | string of digits, leading zeros kept | `zero nau ek` -> `"091"` |
| `money` | `{amount, currency}`; amount is a decimal string in rupees | `sau rupaye pachaas paise` -> `100.50 INR` |
| `time` | `HH:MM`, 24-hour, IST assumed, no date attached | `shaam sawa paanch baje` -> `17:15` |
| `duration` | ISO 8601 duration | `dhai ghante` -> `PT2H30M` |
| `date` | ISO date, resolved against `relative_base` | `3 din baad` -> `2026-11-15` |

Modifiers on any kind:

- **range**: `value` is `{min, max}`; either side may be missing (`tak` gives only `max`).
- **approximate**: `approximate = true` (`ke aaspaas`, `lagbhag`, `kareeb`, `takriban`, `around`).
- **ambiguous**: `value = null`, `ambiguous = true`, `candidates = [...]` lists every reading. Never a silent pick.
- **confidence**: 1.0 for table matches; lowered for edit-distance spelling repairs and weak cues.

## 2. Phenomena

### 2.1 Numerals
| tag | what | examples |
|---|---|---|
| `irregular` | 0-99 are all lexical in Hindi; nothing is composed | `untees` 29, `unhattar` 69, `navaasi` 89 |
| `scale` | sau, hazaar, lakh, crore (arab: see Q9) | `barah hazaar paanch sau` 12500 |
| `lakh-crore` | Indian scales specifically | `teen crore bees lakh` 3,20,00,000 |
| (scale) | hundreds counted past ten | `pachees sau` 2500, `unnees sau sattar` 1970 |
| `indian-grouping` | 2,50,000 and Devanagari digits | `२,५०,०००` |
| `mixed`, `code-switch` | digits + Hindi scale, English + Hindi words | `2 lakh 50 thousand`, `five hazaar` |
| `abbrev` | k, L, cr | `5k`, `2.5L`, `1.2 cr` |
| `digit-seq` | spoken digit strings, double/triple | `double nine triple zero` -> `"99000"` |
| `do-verb` | `do` = "two" vs `do` = verb "give/do" | `do chai de do` -> 2 (once) |
| `spelling`, `noise` | variant-table spellings vs. edit-distance repairs | `hajar`, `lac`, `karod` / `hazzar` |

### 2.2 Fraction idioms
| word | meaning | alone | before a number N | before a scale S |
|---|---|---|---|---|
| sawa | +1/4 | 1.25 | N + 0.25 | 1.25 x S |
| saade | +1/2 | (not used alone) | N + 0.5, N >= 3 | - |
| dedh | 1.5 | 1.5 | - | 1.5 x S |
| dhai / adhai | 2.5 | 2.5 | - | 2.5 x S |
| paune | -1/4 | 0.75 (Q5) | N - 0.25 | 0.75 x S (Q5) |
| aadha, paav | 1/2, 1/4 | 0.5, 0.25 | - | - |

A fraction word binds to the number right after it, and the result multiplies the
scale: `paune do lakh` = 1.75 x 1,00,000 = 1,75,000.

### 2.3 Money
Currency markers: rupaye/rupay/rupiya/rupees, Rs, Rs., INR, the rupee sign, `/-`, paise.
Ranges: `X se Y`, `X-Y`, `tak` (max), `kam se kam` (min), `zyada se zyada` (max).
A trailing scale applies to both ends: `do se teen hazaar` = 2000 to 3000 (Q1).
Two adjacent values form an approximate range: `do dhai hazaar` = 2000 to 2500.

### 2.4 Time
- Day-part words fix AM/PM. Proposed mapping (Q3):

| word | hours it accepts | rule |
|---|---|---|
| subah, savere | 4-11 | AM |
| dopahar | 12, 1-4 | 12:00-16:59 |
| shaam | 4-8 | PM |
| raat | 7-11 -> PM; 12 -> 00:00; 1-4 -> AM | |

- No day-part and hour 1-12: **ambiguous**, both readings returned (`5 baje` -> 05:00, 17:00).
- Hour 13-23 or explicit am/pm: unambiguous.
- `saade/sawa/paune N baje` -> N:30 / N:15 / (N-1):45; `dedh baje` 1:30; `dhai baje` 2:30.
- `N bajke M minute` = N:M. `N bajne mein M minute` = M minutes *before* N.

### 2.5 Durations
Units: second, minute, ghanta, din, hafta, mahina, saal; fraction idioms apply
(`dedh saal` = P1Y6M, `paune ghante` = PT45M).

### 2.6 Dates
| tag | what | rule proposed |
|---|---|---|
| `relative` | aaj, kal, parso, narso | kal = +/-1, parso = +/-2, narso = +/-3 days |
| `tense-cue` | verbs resolve direction | see below |
| `weekday` | bare weekday | next occurrence strictly after base (Q6) |
| `agle`, `pichhle` | next / last | Q7 |
| `offset` | `N din/hafte/mahine/saal baad/pehle` | calendar arithmetic from base |
| `month-relative` | `agle mahine ki 5 tareekh` | |
| `absolute` | `25 disambar 2026`, `12/11/2026` | numeric dates are day-first |

**Direction cues for kal / parso / narso**

| reading | cues (any script) | confidence |
|---|---|---|
| future | -unga/-ungi/-enge, hoga/hogi, `-na hai` (jaana hai), aane wala | high |
| past | tha/thi/the, gaya/gayi, hua/hui, kiya, beeta | high |
| future (weak) | imperative request (`book kar do`), bare present `hai` (Q4) | lowered |
| none | no cue | **ambiguous, both candidates** |

## 3. Out of scope for 0.1 (proposed)

- Units of measure (kilo, gram, litre): the number is parsed, the unit is ignored.
- Slang amounts (peti, khokha), ordinals (pehla, doosra), percentages.
- Date ranges (`agle hafte` as a whole week), recurring times (`har somvaar`).
- Combined date+time as one value: date and time come back as two results.
- Other Indian languages and non-Hindi regional number words.

## Open questions

Please answer these first; they change many cases at once.

| # | Question | My draft answer | Cases |
|---|---|---|---|
| Q1 | `do se teen hazaar`: 2000-3000, or should it be flagged because "2 to 3000" is possible? | 2000-3000, not flagged | MON-031 |
| Q2 | `do teen`, `do chaar`: approximate range, and is `do chaar` really 2-4 or just "a few"? | range, approximate | NUM-078, NUM-080 |
| Q3 | Is the day-part table right? In particular `shaam 4 baje`, `raat 2 baje`, `dopahar 12`. Is bare `12 baje` worth flagging? | as tabled; flagged | TIM-017 and all `daypart` cases |
| Q4 | `kal chhutti hai`, `kal ka ticket book kar do`: accept as future with lower confidence, or keep ambiguous? | future, confidence < 1 | DAT-017, DAT-018 |
| Q5 | Bare `paune` = 0.75 and `paune sau` = 75: natural, or should only `paun`/`pauna` do this? | accept | FRA-006, FRA-016 |
| Q6 | Bare weekday when today is that weekday (`guruvaar` on a Thursday): today, next week, or flag? | flag both | DAT-027 |
| Q7 | `agle shanivaar` said on a Thursday: the coming Saturday or the one in next week? | flag both | DAT-028, DAT-029 |
| Q8 | A date with no year and no cue (`26 January`): flag both years, or assume the next occurrence? | flag both | DAT-052 |
| Q9 | Keep `arab`? Keep `narso`? Keep `2.5L`? Accept `saade ek`? | yes / yes / yes / yes, low confidence | NUM-027, DAT-006, MON-019, FRA-043 |
| Q10 | Romanisation: which spellings do you and people around you actually type? Anything missing from the `spelling` cases? | - | all `spelling` cases |

Q6-Q8 trade safety against convenience: flagging is honest but makes the
library return "ambiguous" more often. An alternative is a caller option
(for example `prefer="future"`) that is off by default.
