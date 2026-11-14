# Taxonomy and canonical forms (draft 2)

Status: **draft 2. Written by an AI agent. Round-1 decisions (Q1-Q9) are applied;
no native speaker has reviewed it yet.** A non-native reviewer checked the
arithmetic and calendar math of the first 292 cases (see
`docs/review/round1_decisions.md`). Naturalness, regional usage and typing
habits are still unchecked.

Cases: `tests/golden/draft_cases.jsonl` (358). Spreadsheet copy:
`docs/review/phase1_cases_review.csv`.

## 1. Kinds and canonical values

| kind | canonical `value` | example |
|---|---|---|
| `number` | integer, or exact decimal (a string in JSON: `"3.25"`) | `dhai lakh` -> 250000 |
| `digits` | string of digits, leading zeros kept | `zero nau ek` -> `"091"` |
| `money` | `{amount, currency}`; amount is a decimal string in rupees | `sau rupaye pachaas paise` -> `100.50 INR` |
| `time` | `HH:MM`, 24-hour, IST assumed | `shaam sawa paanch baje` -> `17:15` |
| `duration` | ISO 8601 duration | `dhai ghante` -> `PT2H30M` |
| `date` | ISO date, resolved against `relative_base` | `3 din baad` -> `2026-11-15` |
| `datetime` | `YYYY-MM-DDTHH:MM`, resolved against a date-time `relative_base` | `do ghante baad` at 10:00 -> `2026-11-12T12:00` |

A date and a time said together are one `datetime` result
(`kal subah 7 baje jaunga` -> `2026-11-13T07:00`).

Modifiers on any kind:

- **range**: `value` is `{min, max}`; either end may be missing. `tak` ("until / up to") gives only `max`.
- **approximate**: `approximate = true` (`ke aaspaas`, `lagbhag`, `kareeb`, `takriban`, `around`, adjacent or hyphenated values).
- **ambiguous**: `value = null`, `ambiguous = true`, `candidates = [...]` lists every reading. Never a silent pick.
- **confidence**: a number in [0, 1]. **It is an ordering, not a calibrated probability**: 1.0 means an exact table match with no weak step; anything lower means some step was a repair or a weak cue. Do not read 0.8 as "80% likely".

Caller option:

- **`prefer="future"`** (or `"past"`), off by default. It resolves dates that are
  ambiguous only for lack of a year or month (`26 January`, `20 tareekh ko`).
  Whether it should also resolve bare `kal`/`parso` is open (Q11).

## 2. Phenomena

### 2.1 Numerals
| tag | what | examples |
|---|---|---|
| `irregular` | 0-99 are all lexical in Hindi | `untees` 29, `unhattar` 69, `navaasi` 89 |
| `scale` | sau, hazaar, lakh, crore, arab | `barah hazaar paanch sau` 12500 |
| `lakh-crore` | Indian scales specifically | `teen crore bees lakh` 3,20,00,000 |
| (scale) | hundreds counted past ten | `pachees sau` 2500, `unnees sau sattar` 1970 |
| `indian-grouping` | 2,50,000 and Devanagari digits | `२,५०,०००` |
| `mixed`, `code-switch` | digits + Hindi scale, English + Hindi, mixed scripts | `2 lakh 50 thousand`, `five hazaar`, `५ lakh` |
| `english-plural` | English plural scale words | `2 lakhs`, `5 crores` |
| `abbrev` | k, cr always; `L` only with a money hint | `5k`, `1.2 cr`, `2.5L` |
| `digit-seq` | spoken digit strings, double/triple | `double nine triple zero` -> `"99000"` |
| `reduplicated` | hyphenated or adjacent pairs = approximate range | `teen-chaar hazaar` 3000-4000, `do teen` 2-3 |
| `do-verb` | `do` = "two" vs the verb "give/do" | `do chai de do` -> 2 (once) |
| `homograph` | words that only look like quantities | `mere saat chalo` (saath = with), `ek baar`, `2.5L paani` |
| `nukta` | ज़ as one code point or as ज + nukta | must parse identically |
| `spelling`, `noise` | variant-table spellings vs. edit-distance repairs | `hajar`, `lac`, `karod` / `hazzar` |

`do chaar` is the idiom "a few": returned as 2-4, approximate, lowered confidence.

### 2.2 Fraction idioms
| word | meaning | alone | before a number N | before a scale S |
|---|---|---|---|---|
| sawa | +1/4 | 1.25 | N + 0.25 | 1.25 x S |
| saade | +1/2 | no | N + 0.5, **only N >= 3** | - |
| dedh | 1.5 | 1.5 | - | 1.5 x S |
| dhai / adhai | 2.5 | 2.5 | - | 2.5 x S |
| paune | -1/4 | 0.75, lowered confidence | N - 0.25 | 0.75 x S |
| paun, pauna | 3/4 | 0.75 | - | - |
| aadha, paav | 1/2, 1/4 | 0.5, 0.25 | - | - |

`saade ek` and `saade do` are rejected (no result): speakers say `dedh` and `dhai`.
A fraction word binds to the number right after it, and the result multiplies
the scale: `paune do lakh` = 1.75 x 1,00,000 = 1,75,000.

### 2.3 Money
Currency markers: rupaye/rupay/rupiya/rupees, Rs, Rs., INR, the rupee sign, `/-`, paise.
Ranges: `X se Y`, `X-Y`, `tak` (max), `kam se kam` (min), `zyada se zyada` (max).
A trailing scale applies to both ends: `do se teen hazaar` = 2000-3000, not flagged.
`paise` with no amount (`mujhe paise de do`) is not a money value.

### 2.4 Time
Day-part words fix AM/PM:

| word | usual hours | result |
|---|---|---|
| subah, savere | 1-11 | AM |
| dopahar | 12, 1-4 | 12:00-16:59 |
| shaam | 4-8 | PM |
| raat | 7-11 -> PM; 12 -> 00:00; 1-4 -> AM | |

- An hour outside a word's usual range still gets a value, with lowered confidence (`shaam 11 baje` -> 23:00).
- No day-part and hour 1-12: **ambiguous**, both readings (`5 baje` -> 05:00, 17:00). Bare `12 baje` is flagged too.
- Hour 13-23 or explicit am/pm: unambiguous.
- `saade/sawa/paune N baje` -> N:30 / N:15 / (N-1):45; `dedh baje` 1:30; `dhai baje` 2:30.
- `N bajke M minute` = N:M. `N bajne mein M minute` = M minutes before N.
- Time ranges: `subah 9 se 11 baje` -> 09:00-11:00; `5 baje tak` -> max only. With no day-part, each candidate is a whole range.
- Relative time: `do ghante baad`, `das minute pehle` -> `datetime` offset from `relative_base`.

### 2.5 Durations
Units: second, minute, ghanta, din, hafta, mahina, saal; fraction idioms apply
(`dedh saal` = P1Y6M, `paune ghante` = PT45M).

### 2.6 Dates
| tag | what | rule |
|---|---|---|
| `relative` | aaj, kal, parso, narso | kal = +/-1, parso = +/-2, narso = +/-3 days (narso: lowered confidence, regional) |
| `tense-cue` | verbs resolve direction | table below |
| `clause-scope` | several dates in one sentence | a cue applies only inside its own clause |
| `weekday` | bare weekday | next occurrence after base; **most recent one if there is a past cue**; flagged if base is that weekday |
| `agle`, `pichhle` | next / last | `agle <weekday>` = first occurrence after base; `agle hafte <weekday>` = in the following Mon-Sun week |
| `offset` | `N din/hafte/mahine/saal baad/pehle` | calendar arithmetic from base |
| `day-of-month` | `20 tareekh ko` | cue decides; no cue = flagged (last or next) unless `prefer` is set |
| `month-relative` | `agle mahine ki 5 tareekh` | |
| `absolute` | `25 disambar 2026`, `12/11/2026` | numeric dates are day-first; no year and no cue = flagged unless `prefer` is set |
| `tak` | `kal tak` | max-only date range; direction rules as for `kal` |

`pehle` is "ago" only after a quantity + unit (`teen din pehle`). At the start of
a clause it means "first" (`pehle teen din rukna`): no date, but a duration.

**Direction cues for kal / parso / narso / weekdays / day-of-month**

| reading | cues (any script) | confidence |
|---|---|---|
| future | -unga/-ungi/-enge, hoga/hogi, `-na hai` (jaana hai), aane wala | 1.0 |
| past | tha/thi/the, gaya/gayi, hua/hui, kiya, beeta | 1.0 |
| future (weak) | imperative request (`book kar do`), bare present `hai` | lowered |
| none | no cue | **ambiguous, all candidates** |

## 3. Out of scope for 0.1

- Units of measure (kilo, gram, litre): the number is parsed, the unit is ignored.
- Slang amounts (peti, khokha), ordinals (pehla, doosra), percentages.
- Whole-period expressions (`agle hafte` as a week), recurring times (`har somvaar`).
- Other Indian languages and non-Hindi regional number words.

## 3a. Where the rules live

Every contested rule below is a row in `src/kitna/data/policy.tsv` (day-part
hours, bare-hour handling, weekday and `agle` rules, no-year and no-month dates,
weak tense cues, whether `prefer` applies to `kal`, and every confidence value).
Changing an answer means editing that file's `value` column. Other behaviours
worth knowing (hyphen ranges, English number words, look-alikes) are described
in [limitations.md](limitations.md).

## 4. Decisions so far

| # | Decision | Decided by |
|---|---|---|
| Q1 | `do se teen hazaar` = 2000-3000, not flagged | reviewer, round 1 |
| Q2 | `do teen` = approx. 2-3; `do chaar` = approx. 2-4, lowered confidence | reviewer, round 1 |
| Q3 | `subah` accepts 1-11; odd day-part/hour pairs get a value with lowered confidence; bare `12 baje` stays flagged | reviewer, round 1 |
| Q4 | `kal ... hai` and imperative requests = future, lowered confidence | reviewer, round 1 |
| Q5 | `paun`/`pauna` = 0.75; `paune sau` = 75; bare `paune` lowered confidence | reviewer, round 1 |
| Q6 | bare weekday on that weekday: flagged | reviewer, round 1 |
| Q8 | no year and no cue: flagged; `prefer="future"` option | reviewer, round 1 |
| Q9 | keep arab; keep narso (lowered confidence); `2.5L` only with money hint; reject `saade ek/do` | reviewer, round 1 |

## 5. Still open (needs a native speaker)

| # | Question | Current draft | Cases |
|---|---|---|---|
| Q3b | Do `shaam 4 baje` (16:00) and `raat 2 baje` (02:00) match real speech? | as shown | TIM-010, TIM-007 |
| Q7 | `agle shanivaar` said on a Thursday: the coming Saturday (reviewer's lean, implemented) or next week's? Ask a few speakers on a Thursday. | coming Saturday, not flagged | DAT-028, DAT-029 |
| Q9b | Is `narso` used where you live, or `tarso`? | narso, lowered confidence | DAT-006 |
| Q10 | Which spellings do you actually type? hazaar/hajar, lakh/lac, baje/bje, chhe/che/chhah, saade/sade/sadhe, dhai/dhaai, paune/pone; do you swap b/w/v? | all listed variants accepted | all `spelling` cases |
| Q11 | Should `prefer="future"` also resolve bare `kal`/`parso`? (new) | yes | DAT-072 |
| Q12 | `ek baar` ("once"): return nothing, or 1? (new; policy row `number.ek_baar`) | nothing | NUM-097 |
