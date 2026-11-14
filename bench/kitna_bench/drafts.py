"""AI-drafted scenario drafts for the main benchmark (v1): everything except the Roman Hinglish line.

For each scenario this file produces the tool set, the gold call, an English line, a
Devanagari line and a neutral brief for the human writer. The Roman Hinglish utterance
is NOT drafted here: native speakers write it from the brief (bench/authoring/guideline.md).

All of it is AI-drafted and unreviewed. Deterministic: no randomness, fixed tables.
"now" is Thursday 2026-11-12, 10:00 IST for every scenario.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from .seed import PAY, REM, SHOP, SUP, TRAVEL

NOW = dt.datetime(2026, 11, 12, 10, 0)
AUTHOR = "ai:draft-v1"
Draft = dict[str, Any]

NAMES = [("Ramesh", "रमेश"), ("Sunita", "सुनीता"), ("Imran", "इमरान"), ("Kavita", "कविता"), ("Arjun", "अर्जुन"),
         ("Meena", "मीना"), ("Farhan", "फ़रहान"), ("Gurpreet", "गुरप्रीत"), ("Lakshmi", "लक्ष्मी"), ("Joseph", "जोसेफ़")]
CITIES = [("Delhi", "दिल्ली"), ("Jaipur", "जयपुर"), ("Pune", "पुणे"), ("Hyderabad", "हैदराबाद"), ("Mumbai", "मुंबई"),
          ("Kolkata", "कोलकाता"), ("Lucknow", "लखनऊ"), ("Varanasi", "वाराणसी"), ("Chennai", "चेन्नई"),
          ("Bhopal", "भोपाल"), ("Patna", "पटना"), ("Indore", "इंदौर")]
PLACES = [("Indiranagar", "इंदिरानगर"), ("airport", "एयरपोर्ट"), ("Koramangala", "कोरमंगला"),
          ("Majestic", "मैजेस्टिक"), ("Whitefield", "व्हाइटफ़ील्ड"), ("station", "स्टेशन"), ("MG Road", "एमजी रोड"),
          ("Jayanagar", "जयनगर")]
# value, English, Devanagari, tags
AMOUNTS = [
    (250000, "2.5 lakh rupees", "ढाई लाख रुपये", ["fraction_value", "lakh_crore"]),
    (1500, "1,500 rupees", "पंद्रह सौ रुपये", ["hundreds_value"]),
    (3750, "3,750 rupees", "पौने चार हज़ार रुपये", ["fraction_value"]),
    (45000, "45,000 rupees", "पैंतालीस हज़ार रुपये", []),
    (150000, "1.5 lakh rupees", "डेढ़ लाख रुपये", ["fraction_value", "lakh_crore"]),
    (599, "599 rupees", "५९९ रुपये", ["devanagari_digits"]),
    (2250, "2,250 rupees", "सवा दो हज़ार रुपये", ["fraction_value"]),
    (12000, "12,000 rupees", "बारह हज़ार रुपये", []),
    (7500, "7,500 rupees", "साढ़े सात हज़ार रुपये", ["fraction_value"]),
    (350, "350 rupees", "साढ़े तीन सौ रुपये", ["fraction_value"]),
    (175000, "1.75 lakh rupees", "पौने दो लाख रुपये", ["fraction_value", "lakh_crore"]),
    (500, "500 rupees", "पाँच सौ रुपये", []),
    (2500, "2,500 rupees", "ढाई हज़ार रुपये", ["fraction_value"]),
    (99, "99 rupees", "निन्यानवे रुपये", []),
    (125000, "1.25 lakh rupees", "सवा लाख रुपये", ["fraction_value", "lakh_crore"]),
    (20000, "20,000 rupees", "बीस हज़ार रुपये", []),
    (850, "850 rupees", "साढ़े आठ सौ रुपये", ["fraction_value"]),
    (10000000, "1 crore rupees", "एक करोड़ रुपये", ["lakh_crore"]),
    (60000, "60,000 rupees", "साठ हज़ार रुपये", []),
    (1100, "1,100 rupees", "ग्यारह सौ रुपये", ["hundreds_value"]),
]
TIMES = [
    ("06:45", "6:45 am", "सुबह पौने सात बजे"), ("18:00", "6 pm", "शाम 6 बजे"), ("21:15", "9:15 pm", "रात सवा नौ बजे"),
    ("15:00", "3 pm", "दोपहर 3 बजे"), ("05:30", "5:30 am", "सुबह साढ़े पाँच बजे"),
    ("16:30", "4:30 pm", "शाम साढ़े चार बजे"), ("11:00", "11 am", "सुबह 11 बजे"),
    ("19:45", "7:45 pm", "शाम पौने आठ बजे"), ("13:30", "1:30 pm", "दोपहर डेढ़ बजे"),
    ("10:30", "10:30 am", "सुबह साढ़े दस बजे"), ("14:30", "2:30 pm", "दोपहर ढाई बजे"),
    ("08:15", "8:15 am", "सुबह सवा आठ बजे"), ("22:00", "10 pm", "रात 10 बजे"), ("12:00", "12 noon", "दोपहर 12 बजे"),
]
# day offset from NOW, English, Devanagari, tags
DAYS = [
    (1, "tomorrow", "कल", ["kal"]), (4, "on Monday", "सोमवार को", ["weekday"]),
    (2, "the day after tomorrow", "परसों", ["parso"]), (8, "on 20 November", "20 नवंबर को", ["absolute_date"]),
    (0, "today", "आज", []), (2, "this Saturday", "इस शनिवार", ["weekday"]),
    (13, "on 25 November", "25 नवंबर को", ["absolute_date"]), (3, "this Sunday", "इस रविवार", ["weekday"]),
    (5, "on Tuesday", "मंगलवार को", ["weekday"]), (19, "on 1 December", "1 दिसंबर को", ["absolute_date"]),
    (6, "on Wednesday", "बुधवार को", ["weekday"]),
]
DURATIONS = [("PT1H30M", "one and a half hours", "डेढ़ घंटे", 90), ("PT45M", "45 minutes", "45 मिनट", 45),
             ("PT2H30M", "two and a half hours", "ढाई घंटे", 150), ("PT1H", "one hour", "एक घंटे", 60),
             ("PT30M", "half an hour", "आधे घंटे", 30), ("PT2H", "2 hours", "दो घंटे", 120)]
COUNTS = [(2, "दो"), (3, "तीन"), (4, "चार"), (5, "पाँच"), (6, "छह"), (12, "बारह"), (25, "पच्चीस"), (1, "एक"),
          (10, "दस")]
ITEMS = [("salt", "नमक के पैकेट", "packets of salt", ["namak", "नमक"]),
         ("pressure cooker", "प्रेशर कुकर", "pressure cookers", ["प्रेशर कुकर", "cooker"]),
         ("laptop", "लैपटॉप", "laptops", ["लैपटॉप"]), ("notebook", "नोटबुक", "notebooks", ["notebooks", "नोटबुक"]),
         ("pen", "पेन", "pens", ["pens", "पेन"]), ("phone", "फ़ोन", "phones", ["फ़ोन", "mobile", "mobile phone"]),
         ("school bag", "स्कूल बैग", "school bags", ["स्कूल बैग", "bag"]),
         ("umbrella", "छाता", "umbrellas", ["छाता", "chhata", "chhatri"]),
         ("water bottle", "पानी की बोतल", "water bottles", ["पानी की बोतल", "bottle", "paani ki bottle"]),
         ("bedsheet", "चादर", "bedsheets", ["चादर", "chadar", "bed sheet"]),
         ("ceiling fan", "सीलिंग फ़ैन", "ceiling fans", ["सीलिंग फ़ैन", "fan", "pankha"]),
         ("cricket bat", "क्रिकेट बैट", "cricket bats", ["क्रिकेट बैट", "bat"])]
BILLERS = [("electricity", "बिजली"), ("mobile", "मोबाइल"), ("dth", "डीटीएच"), ("gas", "गैस"), ("water", "पानी"),
           ("broadband", "ब्रॉडबैंड")]
CLASSES = [("3A", "3A", "3A"), ("SL", "sleeper class", "स्लीपर"), ("2A", "2A", "2A"), ("CC", "chair car", "चेयर कार"),
           ("1A", "1A", "1A")]
TITLES = [("call the doctor", "डॉक्टर को कॉल करने"), ("take my medicine", "दवाई लेने"),
          ("pay the rent", "किराया देने"), ("pick up the parcel", "पार्सल लेने"),
          ("water the plants", "पौधों को पानी देने"), ("book the gas cylinder", "गैस सिलेंडर बुक करने")]
EVENTS = [("team meeting", "टीम मीटिंग"), ("yoga session", "योग सेशन"),
          ("parent-teacher meeting", "पैरेंट-टीचर मीटिंग"), ("dentist appointment", "डेंटिस्ट का अपॉइंटमेंट"),
          ("family dinner", "फ़ैमिली डिनर")]
PAIRS = [(2, 3, "thousand", "हज़ार", "दो-तीन"), (4, 5, "hundred", "सौ", "चार-पाँच"),
         (10, 12, "thousand", "हज़ार", "दस-बारह")]
BARE_HOURS = [(5, "5"), (7, "7"), (8, "8"), (9, "9"), (6, "6")]

# Negative items: (domain, brief, English, Devanagari, tags). No tool should be called.
NEGATIVES = [
    ("payments", "Ask a general question about fixed-deposit interest rates. You do not want any action.",
     "Which bank gives the best interest on a fixed deposit these days?",
     "आजकल एफ़डी पर सबसे अच्छा ब्याज कौन सा बैंक देता है?", []),
    ("payments", "Tell the assistant you already paid the electricity bill yesterday. No action wanted.",
     "I already paid the electricity bill yesterday.", "बिजली का बिल मैंने कल ही भर दिया था", ["kal"]),
    ("payments", "Complain, in passing, that things have become expensive. Mention no amount to pay or send.",
     "Everything has become so expensive these days.", "आजकल सब कुछ कितना महँगा हो गया है", []),
    ("payments", "Ask what UPI is, as a general question.", "What exactly is UPI and how does it work?",
     "यूपीआई आख़िर क्या होता है और कैसे काम करता है?", []),
    ("travel", "Ask a friend-style question: will you come to Goa with me? No booking wanted.",
     "Will you come to Goa with me?", "मेरे साथ गोवा चलोगे?", ["lookalike_saath"]),
    ("travel", "Say that your train was two hours late yesterday. You are only telling, not asking for anything.",
     "My train was two hours late yesterday.", "कल मेरी ट्रेन दो घंटे लेट थी", ["kal", "past_statement"]),
    ("travel", "Ask which is the best season to visit Jaipur.", "What is the best season to visit Jaipur?",
     "जयपुर घूमने के लिए सबसे अच्छा मौसम कौन सा है?", []),
    ("travel", "Say you are tired of travelling and want to stay home. No booking wanted.",
     "I am tired of travelling, I just want to stay home.", "मैं सफ़र से थक गया हूँ, बस घर पर रहना है", []),
    ("reminders", "Ask the assistant to explain once more how alarms work. No alarm should be set.",
     "Tell me once more, how does the alarm work?", "मुझे एक बार फिर से बताओ, अलार्म कैसे काम करता है?",
     ["lookalike_ek_baar"]),
    ("reminders", "Say that you woke up at 5 this morning. You are only telling.",
     "I woke up at 5 this morning.", "आज सुबह मैं 5 बजे उठ गया था", ["past_statement"]),
    ("reminders", "Ask what day of the week it is today.", "What day is it today?", "आज कौन सा दिन है?", []),
    ("reminders", "Say that yesterday's meeting went well. No event should be created.",
     "Yesterday's meeting went really well.", "कल की मीटिंग बहुत अच्छी रही", ["kal", "past_statement"]),
    ("shopping", "Say you did not like a shirt and tell the assistant to leave it. No order wanted.",
     "I did not like this shirt, leave it.", "यह शर्ट मुझे पसंद नहीं आई, रहने दो", ["lookalike_do"]),
    ("shopping", "Ask whether cotton or polyester is better for summer.",
     "Is cotton or polyester better for summer?", "गर्मियों के लिए कॉटन अच्छा है या पॉलिएस्टर?", []),
    ("shopping", "Say that you bought two phones last year. You are only telling.",
     "I bought two phones last year.", "पिछले साल मैंने दो फ़ोन ख़रीदे थे", ["past_statement"]),
    ("shopping", "Say you will think about it and decide later. No order wanted.",
     "Let me think about it, I will decide later.", "सोचकर बताता हूँ, बाद में तय करूँगा", []),
    ("support", "Thank the assistant and say the problem is solved.", "Thanks, the issue is resolved now.",
     "शुक्रिया, अब समस्या ठीक हो गई है", []),
    ("support", "Ask what the customer-care working hours are.", "What are your customer care working hours?",
     "आपके कस्टमर केयर का समय क्या है?", []),
    ("support", "Say that the delivery person was very polite. No ticket wanted.",
     "The delivery person was very polite.", "डिलीवरी वाला बहुत विनम्र था", []),
    ("support", "Greet the assistant and ask how it is doing.", "Hello, how are you?", "नमस्ते, आप कैसे हैं?", []),
]


def _inr(n: int) -> str:
    """Indian digit grouping: 250000 -> ₹2,50,000."""
    s = str(n)
    if len(s) <= 3:
        return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts: list[str] = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    parts.insert(0, head)
    return "₹" + ",".join(parts) + "," + tail


def _date(offset: int) -> dt.date:
    return (NOW + dt.timedelta(days=offset)).date()


def _show_date(d: dt.date) -> str:
    return d.strftime("%a %d %b %Y")


def _show_time(hhmm: str) -> str:
    t = dt.time.fromisoformat(hhmm)
    return t.strftime("%I:%M %p").lstrip("0")


class _Builder:
    def __init__(self) -> None:
        self.rows: list[Draft] = []
        self.counter: dict[str, int] = {}
        self.k = 0

    def pick(self, table: list[Any], stride: int = 1, offset: int = 0) -> Any:
        return table[(self.k * stride + offset) % len(table)]

    def add(self, domain: str, tools: list[str], tool: str | None, args: dict[str, str], clarify: list[str],
            tags: list[str], brief: str, en: str, deva: str, aliases: dict[str, list[str]] | None = None,
            english_gold: dict[str, Any] | None = None) -> None:
        short = {"payments": "pay", "travel": "trv", "reminders": "rem", "shopping": "shp", "support": "sup"}[domain]
        self.counter[short] = self.counter.get(short, 0) + 1
        behavior = "abstain" if tool is None else ("clarify" if clarify else "call")
        self.rows.append({
            "scenario_id": f"v1-{short}-{self.counter[short]:03d}", "domain": domain, "tools": tools,
            "now": NOW.strftime("%Y-%m-%dT%H:%M"), "expected_behavior": behavior, "gold_tool": tool,
            "gold_arguments": args, "aliases": aliases or {}, "clarify_about": clarify,
            "phenomena": sorted(set(tags + (["variant_specific_gold"] if english_gold else []))),
            "brief": brief, "english": en, "devanagari": deva, "english_gold": english_gold,
            "provenance": "ai_drafted", "author_id": AUTHOR,
        })
        self.k += 1


HEAD = "Today is Thu 12 Nov 2026, 10:00 am. "


def build_drafts() -> list[Draft]:
    b = _Builder()

    def al(**kw: tuple[str, str]) -> dict[str, list[str]]:
        return {k: [v[1]] for k, v in kw.items()}

    # ------------------------------------------------------------ payments: 22 call
    for n in range(22):
        name, (amt, amt_en, amt_hi, atags) = NAMES[(n * 3 + n // 10) % 10], AMOUNTS[(n * 7 + 2) % 20]
        biller, day = b.pick(BILLERS), [d for d in DAYS if d[0] >= 1][n % 10]
        kind = n % 5 if n < 10 else n % 4      # only two balance questions: there are only two accounts
        if kind == 0:
            b.add("payments", PAY, "send_money", {"payee_name": name[0], "amount_inr": str(amt)}, [], atags,
                  HEAD + f"Ask to send money now. Payee: {name[0]}. Amount: {_inr(amt)}.",
                  f"Send {amt_en} to {name[0]}.", f"{name[1]} को {amt_hi} भेज दो", al(payee_name=name))
        elif kind == 1:
            b.add("payments", PAY, "send_money",
                  {"payee_name": name[0], "amount_inr": str(amt), "schedule_date": _date(day[0]).isoformat()}, [],
                  atags + day[3],
                  HEAD + f"Ask to send money on a later day. Payee: {name[0]}. Amount: {_inr(amt)}. "
                  f"Day: {_show_date(_date(day[0]))}.",
                  f"Send {amt_en} to {name[0]} {day[1]}.", f"{day[2]} {name[1]} को {amt_hi} भेजने हैं",
                  al(payee_name=name))
        elif kind == 2:
            b.add("payments", PAY, "pay_bill", {"biller": biller[0], "amount_inr": str(amt)}, [], atags,
                  HEAD + f"Ask to pay a bill now. Bill: {biller[0]}. Amount: {_inr(amt)}.",
                  f"Pay my {biller[0]} bill of {amt_en}.", f"मेरा {biller[1]} का {amt_hi} का बिल भर दो")
        elif kind == 3:
            b.add("payments", PAY, "pay_bill",
                  {"biller": biller[0], "amount_inr": str(amt), "due_date": _date(day[0]).isoformat()}, [],
                  atags + day[3],
                  HEAD + f"Ask to pay a bill on a later day. Bill: {biller[0]}. Amount: {_inr(amt)}. "
                  f"Day: {_show_date(_date(day[0]))}.",
                  f"Pay the {biller[0]} bill of {amt_en} {day[1]}.", f"{day[2]} {biller[1]} का {amt_hi} का बिल भर देना")
        else:
            acct = [("savings", "बचत"), ("current", "करंट")][(n // 5) % 2]
            wording = ("What is the balance in my {a} account?", "मेरे {h} खाते में कितना बैलेंस है?")
            b.add("payments", PAY, "check_balance", {"account_type": acct[0]}, [], [],
                  HEAD + f"Ask for the balance of your {acct[0]} account.",
                  wording[0].format(a=acct[0]), wording[1].format(h=acct[1]))
    # payments: 6 clarify
    for n in range(6):
        name, biller = b.pick(NAMES, 1, 3), b.pick(BILLERS, 1, 2)
        if n % 3 == 0:
            b.add("payments", PAY, "send_money", {"payee_name": name[0]}, ["amount_inr"], ["missing_argument"],
                  HEAD + f"Ask to send money to {name[0]} but do NOT say how much.",
                  f"Send some money to {name[0]}.", f"{name[1]} को पैसे भेज दो", al(payee_name=name))
        elif n % 3 == 1:
            lo, hi, unit_en, unit_hi, pair_hi = PAIRS[n // 3 % 3]
            b.add("payments", PAY, "send_money", {"payee_name": name[0]}, ["amount_inr"], ["approximate_pair"],
                  HEAD + f"Ask to send money to {name[0]}. Give the amount only loosely, as "
                  f"'{lo} or {hi} {unit_en}' (do not give one exact figure).",
                  f"Send {lo} or {hi} {unit_en} rupees to {name[0]}.", f"{name[1]} को {pair_hi} {unit_hi} भेज दो",
                  al(payee_name=name))
        else:
            b.add("payments", PAY, "pay_bill", {"biller": biller[0]}, ["amount_inr"], ["missing_argument"],
                  HEAD + f"Ask to pay your {biller[0]} bill but do NOT say the amount.",
                  f"Pay my {biller[0]} bill.", f"मेरा {biller[1]} का बिल भर दो")
    # ------------------------------------------------------------ travel: 22 call
    for n in range(22):
        a, c = CITIES[n % 12], CITIES[(n * 5 + 7) % 12]
        if a == c:
            c = CITIES[(n + 1) % 12]
        p, q = PLACES[n % 8], PLACES[(n * 3 + 5) % 8]
        if p == q:
            q = PLACES[(n + 1) % 8]
        day, (hhmm, t_en, t_hi) = DAYS[(n * 2 + 1) % 11], TIMES[(n * 3) % 14]
        if day[0] == 0 and hhmm <= "10:00":
            day = DAYS[0]
        cnt, cls = COUNTS[n % 5], CLASSES[n % 5]
        amt, amt_en, amt_hi, atags = AMOUNTS[(n * 7 + 8) % 20]
        d = _date(day[0])
        kind = n % 4
        if kind == 0:
            b.add("travel", TRAVEL, "book_train",
                  {"from_city": a[0], "to_city": c[0], "travel_date": d.isoformat(), "passengers": str(cnt[0]),
                   "travel_class": cls[0]}, [], day[3],
                  HEAD + f"Ask to book train tickets. From: {a[0]}. To: {c[0]}. Day: {_show_date(d)}. "
                  f"Passengers: {cnt[0]}. Class: {cls[0]}.",
                  f"Book {cnt[0]} tickets in {cls[1]} from {a[0]} to {c[0]} {day[1]}.",
                  f"{day[2]} {a[1]} से {c[1]} के {cnt[1]} टिकट {cls[2]} में बुक कर दो", al(from_city=a, to_city=c))
        elif kind == 1:
            b.add("travel", TRAVEL, "book_cab",
                  {"pickup": p[0], "drop": q[0], "pickup_time": f"{d.isoformat()}T{hhmm}"}, [], day[3] + ["time"],
                  HEAD + f"Ask to book a cab. From: {p[0]}. To: {q[0]}. Day: {_show_date(d)}. "
                  f"Time: {_show_time(hhmm)}.",
                  f"Book a cab from {p[0]} to {q[0]} {day[1]} at {t_en}.",
                  f"{day[2]} {t_hi} {p[1]} से {q[1]} के लिए कैब बुक कर दो", al(pickup=p, drop=q))
        elif kind == 2:
            b.add("travel", TRAVEL, "search_flights",
                  {"from_city": a[0], "to_city": c[0], "travel_date": d.isoformat()}, [], day[3],
                  HEAD + f"Ask to see flights. From: {a[0]}. To: {c[0]}. Day: {_show_date(d)}.",
                  f"Show flights from {a[0]} to {c[0]} {day[1]}.", f"{day[2]} {a[1]} से {c[1]} की फ़्लाइट दिखाओ",
                  al(from_city=a, to_city=c))
        else:
            b.add("travel", TRAVEL, "search_flights",
                  {"from_city": a[0], "to_city": c[0], "travel_date": d.isoformat(), "max_price_inr": str(amt)}, [],
                  day[3] + atags,
                  HEAD + f"Ask to see flights under a price. From: {a[0]}. To: {c[0]}. Day: {_show_date(d)}. "
                  f"Highest fare: {_inr(amt)}.",
                  f"Show flights from {a[0]} to {c[0]} {day[1]} under {amt_en}.",
                  f"{day[2]} {a[1]} से {c[1]} की फ़्लाइट दिखाओ, {amt_hi} से कम में", al(from_city=a, to_city=c))
    # travel: 6 clarify
    for n in range(6):
        a, c = CITIES[(n * 2 + 3) % 12], CITIES[(n * 2 + 8) % 12]
        p, q = PLACES[(n + 2) % 8], PLACES[(n + 5) % 8]
        cnt, cls = COUNTS[(n + 1) % 5], CLASSES[(n + 2) % 5]
        if n % 3 == 0:
            hour = BARE_HOURS[n // 3]
            b.add("travel", TRAVEL, "book_cab", {"pickup": p[0], "drop": q[0]}, ["pickup_time"], ["bare_hour", "kal"],
                  HEAD + f"Ask for a cab from {p[0]} to {q[0]} tomorrow at {hour[1]} o'clock. Say only the number: "
                  "no 'morning', 'evening', 'am' or 'pm'.",
                  f"I need a cab from {p[0]} to {q[0]} tomorrow at {hour[1]}.",
                  f"कल {hour[1]} बजे {p[1]} से {q[1]} के लिए कैब चाहिए", al(pickup=p, drop=q))
        elif n % 3 == 1:
            b.add("travel", TRAVEL, "book_train",
                  {"from_city": a[0], "to_city": c[0], "passengers": str(cnt[0]), "travel_class": cls[0]},
                  ["travel_date"], ["missing_argument"],
                  HEAD + f"Ask to book train tickets but do NOT say the day. From: {a[0]}. To: {c[0]}. "
                  f"Passengers: {cnt[0]}. Class: {cls[0]}.",
                  f"Book {cnt[0]} tickets in {cls[1]} from {a[0]} to {c[0]}.",
                  f"{a[1]} से {c[1]} के {cnt[1]} टिकट {cls[2]} में बुक कर दो", al(from_city=a, to_city=c))
        else:
            b.add("travel", TRAVEL, "search_flights", {"from_city": a[0], "to_city": c[0]}, ["travel_date"],
                  ["missing_argument"],
                  HEAD + f"Ask to see flights from {a[0]} to {c[0]} but do NOT say the day.",
                  f"Show me flights from {a[0]} to {c[0]}.", f"{a[1]} से {c[1]} की फ़्लाइट दिखाओ",
                  al(from_city=a, to_city=c))
    # ------------------------------------------------------------ reminders: 22 call
    for n in range(22):
        day, (hhmm, t_en, t_hi) = DAYS[(n * 3) % 11], TIMES[(n * 5 + 2) % 14]
        if day[0] == 0 and hhmm <= "10:00":
            day = DAYS[2]
        d = _date(day[0])
        title, event = TITLES[n % 6], EVENTS[n % 5]
        dur = DURATIONS[n % 6]
        kind = n % 5
        if kind == 0:
            b.add("reminders", REM, "set_alarm", {"time": hhmm}, [], ["time"],
                  HEAD + f"Ask to set an alarm. Time: {_show_time(hhmm)}.",
                  f"Set an alarm for {t_en}.", f"{t_hi} का अलार्म लगा दो")
        elif kind == 1:
            b.add("reminders", REM, "set_reminder", {"at": f"{d.isoformat()}T{hhmm}"}, [], day[3] + ["time"],
                  HEAD + f"Ask for a reminder to {title[0]}. Day: {_show_date(d)}. Time: {_show_time(hhmm)}.",
                  f"Remind me {day[1]} at {t_en} to {title[0]}.", f"{day[2]} {t_hi} {title[1]} का रिमाइंडर लगा दो")
        elif kind == 2:
            b.add("reminders", REM, "create_event",
                  {"date": d.isoformat(), "start_time": hhmm, "duration": dur[0]}, [],
                  day[3] + ["time", "duration"],
                  HEAD + f"Ask to add a calendar event: {event[0]}. Day: {_show_date(d)}. "
                  f"Start: {_show_time(hhmm)}. Length: {dur[3]} minutes.",
                  f"Add a {event[0]} {day[1]} at {t_en} for {dur[1]}.",
                  f"{day[2]} {t_hi} {dur[2]} के लिए {event[1]} कैलेंडर में डाल दो")
        elif kind == 3:
            b.add("reminders", REM, "create_event", {"date": d.isoformat(), "start_time": hhmm}, [],
                  day[3] + ["time"],
                  HEAD + f"Ask to add a calendar event: {event[0]}. Day: {_show_date(d)}. "
                  f"Start: {_show_time(hhmm)}. Do not mention how long it lasts.",
                  f"Add a {event[0]} {day[1]} at {t_en}.", f"{day[2]} {t_hi} {event[1]} कैलेंडर में डाल दो")
        else:
            at = NOW + dt.timedelta(minutes=dur[3])
            b.add("reminders", REM, "set_reminder", {"at": at.strftime("%Y-%m-%dT%H:%M")}, [],
                  ["relative_time", "duration"],
                  HEAD + f"Ask for a reminder to {title[0]}, {dur[3]} minutes from now. Say it as a length of time "
                  "from now, not as a clock time.",
                  f"Remind me in {dur[1]} to {title[0]}.", f"{dur[2]} बाद {title[1]} का रिमाइंडर लगा दो")
    # reminders: 6 clarify
    for n in range(6):
        title, event = TITLES[(n + 3) % 6], EVENTS[(n + 2) % 5]
        day = [d for d in DAYS if d[0] >= 1][(n * 3 + 1) % 10]
        d = _date(day[0])
        if n % 3 == 0:
            hour = BARE_HOURS[2 + n // 3]
            b.add("reminders", REM, "set_reminder", {}, ["at"], ["bare_hour"],
                  HEAD + f"Ask for a reminder to {title[0]} at {hour[1]} o'clock. Say only the number: no day, no "
                  "'morning', 'evening', 'am' or 'pm'.",
                  f"Remind me at {hour[1]} to {title[0]}.", f"{hour[1]} बजे {title[1]} का रिमाइंडर लगा दो")
        elif n % 3 == 1:
            b.add("reminders", REM, "create_event", {"date": d.isoformat()}, ["start_time"],
                  ["missing_argument"] + day[3],
                  HEAD + f"Ask to add a calendar event: {event[0]}. Day: {_show_date(d)}. Do NOT say the time.",
                  f"Put a {event[0]} on my calendar {day[1]}.", f"{day[2]} {event[1]} कैलेंडर में डाल दो")
        else:
            b.add("reminders", REM, "set_reminder", {}, ["at"], ["missing_argument"] + day[3],
                  HEAD + f"Ask for a reminder to {title[0]}. Day: {_show_date(d)}. Do NOT say the time.",
                  f"Remind me {day[1]} to {title[0]}.", f"{day[2]} {title[1]} का रिमाइंडर लगा दो")
    # ------------------------------------------------------------ shopping: 22 call
    for n in range(22):
        item, cnt = ITEMS[n % 12], COUNTS[(n * 2 + 1) % 9]
        amt, amt_en, amt_hi, atags = AMOUNTS[(n * 3 + 1) % 20]
        oid = f"OD-{41357 + n * 2671}"
        ali = {"item": item[3]}
        kind = n % 4
        if kind == 0:
            b.add("shopping", SHOP, "place_order", {"item": item[0], "quantity": str(cnt[0])}, [], ["count"],
                  HEAD + f"Ask to order a product. Product: {item[0]}. How many: {cnt[0]}.",
                  f"Order {cnt[0]} {item[2] if cnt[0] > 1 else item[0]}.", f"{cnt[1]} {item[1]} ऑर्डर कर दो", ali)
        elif kind == 1:
            b.add("shopping", SHOP, "place_order",
                  {"item": item[0], "quantity": str(cnt[0]), "max_price_inr": str(amt)}, [], ["count"] + atags,
                  HEAD + f"Ask to order a product with a price limit. Product: {item[0]}. How many: {cnt[0]}. "
                  f"Highest price for one: {_inr(amt)}.",
                  f"Order {cnt[0]} {item[2] if cnt[0] > 1 else item[0]}, not above {amt_en} each.",
                  f"{cnt[1]} {item[1]} ऑर्डर कर दो, एक का दाम {amt_hi} से ज़्यादा न हो", ali)
        elif kind == 2:
            b.add("shopping", SHOP, "set_price_alert", {"item": item[0], "target_price_inr": str(amt)}, [], atags,
                  HEAD + f"Ask to be told when a product reaches a price. Product: {item[0]}. Price: {_inr(amt)}.",
                  f"Alert me when the {item[0]} price drops to {amt_en}.",
                  f"जब {item[1]} का दाम {amt_hi} हो जाए तो बता देना", ali)
        else:
            b.add("shopping", SHOP, "track_order", {"order_id": oid}, [], ["id"],
                  HEAD + f"Ask where your order is. Order ID: {oid}.",
                  f"Where is my order {oid}?", f"मेरा ऑर्डर {oid} कहाँ तक पहुँचा?")
    # shopping: 6 clarify
    for n in range(6):
        item = ITEMS[(n * 5 + 2) % 12]
        ali = {"item": item[3]}
        if n % 3 == 0:
            lo, hi, pair_hi = [(4, 5, "चार-पाँच"), (2, 3, "दो-तीन")][n // 3]
            b.add("shopping", SHOP, "place_order", {"item": item[0]}, ["quantity"], ["approximate_pair"],
                  HEAD + f"Ask to order {item[0]}. Give the number only loosely, as '{lo} or {hi}'.",
                  f"Order {lo} or {hi} {item[2]}.", f"{pair_hi} {item[1]} ऑर्डर कर दो", ali)
        elif n % 3 == 1:
            b.add("shopping", SHOP, "set_price_alert", {"item": item[0]}, ["target_price_inr"], ["missing_argument"],
                  HEAD + f"Ask to be told when the {item[0]} gets cheaper. Do NOT name a price.",
                  f"Tell me when the {item[0]} gets cheaper.", f"{item[1]} सस्ता हो तो बता देना", ali)
        else:
            ask, en, hi_ = [("Ask where your order is", "Where is my order?", "मेरा ऑर्डर कहाँ है?"),
                            ("Tell the assistant to track your order", "Track my order.", "मेरा ऑर्डर ट्रैक करो")][n // 3]
            b.add("shopping", SHOP, "track_order", {}, ["order_id"], ["missing_argument"],
                  HEAD + f"{ask}, without giving any order ID.", en, hi_)
    # ------------------------------------------------------------ support: 22 call
    for n in range(22):
        amt, amt_en, amt_hi, atags = AMOUNTS[(n * 9 + 5 + n // 20) % 20]
        oid = f"OD-{50211 + n * 1933}"
        day, (hhmm, t_en, t_hi) = DAYS[(n * 4 + 2) % 11], TIMES[(n * 3 + 1) % 14]
        if day[0] == 0 and hhmm <= "10:00":
            day = DAYS[0]
        d = _date(day[0])
        kind = n % 5
        if kind == 0:
            b.add("support", SUP, "raise_ticket",
                  {"category": "refund", "order_id": oid, "amount_inr": str(amt)}, [], ["id"] + atags,
                  HEAD + f"Ask for a refund. Order ID: {oid}. Amount: {_inr(amt)}.",
                  f"I want a refund of {amt_en} for order {oid}.", f"ऑर्डर {oid} का {amt_hi} का रिफ़ंड चाहिए")
        elif kind == 1:
            b.add("support", SUP, "raise_ticket", {"category": "billing", "amount_inr": str(amt)}, [], atags,
                  HEAD + f"Complain that your bill charged you too much. Extra amount: {_inr(amt)}.",
                  f"I was charged {amt_en} extra on my bill.", f"मेरे बिल में {amt_hi} ज़्यादा कट गए हैं")
        elif kind == 2:
            b.add("support", SUP, "request_callback", {"callback_time": f"{d.isoformat()}T{hhmm}"}, [],
                  day[3] + ["time"],
                  HEAD + f"Ask for a phone call back. Day: {_show_date(d)}. Time: {_show_time(hhmm)}.",
                  f"Call me back {day[1]} at {t_en}.", f"{day[2]} {t_hi} मुझे कॉलबैक कर देना")
        elif kind == 3:
            b.add("support", SUP, "check_refund_status", {"order_id": oid}, [], ["id"],
                  HEAD + f"Ask about the status of your refund. Order ID: {oid}.",
                  f"What is the refund status of order {oid}?", f"ऑर्डर {oid} का रिफ़ंड कब तक आएगा?")
        else:
            b.add("support", SUP, "raise_ticket", {"category": "delivery", "order_id": oid}, [], ["id"],
                  HEAD + f"Complain that an order has not arrived. Order ID: {oid}.",
                  f"Order {oid} has not been delivered yet.", f"ऑर्डर {oid} अभी तक डिलीवर नहीं हुआ है")
    # support: 6 clarify
    for n in range(6):
        oid = f"OD-{61007 + n * 3119}"
        if n < 2:
            hour = BARE_HOURS[n]
            b.add("support", SUP, "request_callback", {}, ["callback_time"], ["bare_hour", "kal"],
                  HEAD + f"Ask for a phone call back tomorrow at {hour[1]} o'clock. Say only the number: no "
                  "'morning', 'evening', 'am' or 'pm'.",
                  f"Call me back tomorrow at {hour[1]}.", f"कल {hour[1]} बजे मुझे कॉलबैक कर देना")
        elif n == 2:
            b.add("support", SUP, "raise_ticket", {"category": "refund"}, ["order_id"], ["missing_argument"],
                  HEAD + "Ask for a refund without saying which order.", "I need a refund.", "मुझे रिफ़ंड चाहिए")
        elif n == 3:
            b.add("support", SUP, "check_refund_status", {}, ["order_id"], ["missing_argument"],
                  HEAD + "Ask when your refund will come, without saying which order.",
                  "When will I get my refund?", "मेरा रिफ़ंड कब आएगा?")
        else:
            # Hindi 'kal' is yesterday or tomorrow; the English line has to pick one, so its gold differs.
            off, en_word = [(-1, "yesterday's"), (1, "tomorrow's")][n - 4]
            b.add("support", SUP, "raise_ticket", {"category": "delivery", "order_id": oid}, ["incident_date"], ["kal"],
                  HEAD + f"Report a problem with a delivery of order {oid}. For the day, use only the word 'kal' "
                  "and give no other hint about whether it already happened (no 'tha', 'hoga', 'aayi', 'aayegi').",
                  f"There is a problem with {en_word} delivery of order {oid}.",
                  f"ऑर्डर {oid} की कल की डिलीवरी में दिक़्क़त है",
                  english_gold={"expected_behavior": "call", "clarify_about": [],
                                "gold_arguments": {"category": "delivery", "order_id": oid,
                                                   "incident_date": _date(off).isoformat()}})
    # ------------------------------------------------------------ negatives: 4 per domain
    tools = {"payments": PAY, "travel": TRAVEL, "reminders": REM, "shopping": SHOP, "support": SUP}
    for domain, brief, en, deva, tags in NEGATIVES:
        b.add(domain, tools[domain], None, {}, [], ["negative"] + tags, HEAD + brief + " (The assistant should "
              "not call any tool.)", en, deva)
    return sorted(b.rows, key=lambda r: r["scenario_id"])
