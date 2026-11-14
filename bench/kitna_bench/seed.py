"""The AI-drafted seed set: 40 scenarios x 3 variants, for testing the pipeline only.

Every utterance, tool schema and gold value here was written by an AI model and
has not been reviewed by a native speaker. The seed set is never reported as
benchmark results. `python scripts/bench.py seed` rewrites bench/items/seed_v0.jsonl
from this file; the test suite checks that the two agree.

"now" for every scenario is Thursday 2026-11-12, 10:00 IST.
"""
from __future__ import annotations

from typing import Any

from .items import Item, load_tools, tool_for_item

NOW = "2026-11-12T10:00"
AUTHOR = "ai:seed-v0"
PAY = ["send_money", "pay_bill", "check_balance"]
TRAVEL = ["book_train", "book_cab", "search_flights"]
REM = ["set_reminder", "create_event", "set_alarm"]
SHOP = ["place_order", "track_order", "set_price_alert"]
SUP = ["raise_ticket", "request_callback", "check_refund_status"]

# Names and places as they may appear in a model's arguments.
ALIASES: dict[str, list[str]] = {
    "Ramesh": ["रमेश"], "Sunita": ["सुनीता"], "Imran": ["इमरान"], "Kavita": ["कविता"], "Arjun": ["अर्जुन"],
    "Delhi": ["दिल्ली", "New Delhi", "NDLS"], "Jaipur": ["जयपुर"], "Pune": ["पुणे"], "Hyderabad": ["हैदराबाद"],
    "Mumbai": ["मुंबई", "Bombay"], "Kolkata": ["कोलकाता", "Calcutta"], "Lucknow": ["लखनऊ"],
    "Varanasi": ["वाराणसी", "Banaras", "Benares"], "Indiranagar": ["इंदिरानगर"],
    "airport": ["एयरपोर्ट", "the airport", "hawai adda"], "Koramangala": ["कोरमंगला"], "Majestic": ["मैजेस्टिक"],
    "Whitefield": ["व्हाइटफ़ील्ड"], "station": ["स्टेशन", "railway station", "the station"],
    "salt": ["namak", "नमक"], "pressure cooker": ["प्रेशर कुकर", "cooker"], "laptop": ["लैपटॉप"],
    "notebook": ["notebooks", "नोटबुक", "copy"], "pen": ["pens", "पेन"], "phone": ["फ़ोन", "mobile", "mobile phone"],
}

# (scenario, tools, gold tool, gold arguments, clarify_about, phenomena, english, roman, devanagari)
Row = tuple[str, list[str], "str | None", dict[str, str], list[str], list[str], str, str, str]
ROWS: list[Row] = [
    # ---- payments
    ("seed-pay-001", PAY, "send_money", {"payee_name": "Ramesh", "amount_inr": "250000"}, [],
     ["fraction_idiom", "lakh"],
     "Send 2.5 lakh rupees to Ramesh.", "Ramesh ko dhai lakh rupaye bhej do", "रमेश को ढाई लाख रुपये भेज दो"),
    ("seed-pay-002", PAY, "send_money", {"payee_name": "Sunita", "amount_inr": "1500", "schedule_date": "2026-11-13"},
     [], ["kal", "hundreds_idiom"],
     "Send 1,500 rupees to Sunita tomorrow.", "Sunita ko kal pandrah sau rupaye bhejna hai",
     "सुनीता को कल पंद्रह सौ रुपये भेजना है"),
    ("seed-pay-003", PAY, "pay_bill", {"biller": "electricity", "amount_inr": "3750"}, [], ["fraction_idiom"],
     "Pay the electricity bill of 3,750 rupees.", "Bijli ka bill bhar do, paune chaar hazaar ka hai",
     "बिजली का बिल भर दो, पौने चार हज़ार का है"),
    ("seed-pay-004", PAY, "pay_bill", {"biller": "mobile", "amount_inr": "599"}, [], ["devanagari_digits"],
     "Pay my mobile bill, 599 rupees.", "Mera mobile ka bill pay kar do, 599 rupaye",
     "मेरा मोबाइल का बिल भर दो, ५९९ रुपये"),
    ("seed-pay-005", PAY, "send_money", {"payee_name": "Imran", "amount_inr": "150000"}, [],
     ["fraction_idiom", "lakh"],
     "Transfer one and a half lakh rupees to Imran.", "Imran ko dedh lakh transfer kar do",
     "इमरान को डेढ़ लाख ट्रांसफ़र कर दो"),
    ("seed-pay-006", PAY, "send_money", {"payee_name": "Kavita"}, ["amount_inr"], ["missing_argument"],
     "Send money to Kavita.", "Kavita ko paise bhej do", "कविता को पैसे भेज दो"),
    ("seed-pay-007", PAY, "send_money", {"payee_name": "Arjun"}, ["amount_inr"], ["approximate_pair"],
     "Send two or three thousand rupees to Arjun.", "Arjun ko do teen hazaar bhej do",
     "अर्जुन को दो-तीन हज़ार भेज दो"),
    ("seed-pay-008", PAY, None, {}, [], ["negative"],
     "What is a good interest rate for a fixed deposit?", "FD ka achha interest rate kya hota hai?",
     "एफ़डी की अच्छी ब्याज दर क्या होती है?"),
    # ---- travel
    ("seed-trv-001", TRAVEL, "book_train",
     {"from_city": "Delhi", "to_city": "Jaipur", "travel_date": "2026-11-14", "passengers": "2", "travel_class": "3A"},
     [], ["weekday"],
     "Book 2 tickets in 3A from Delhi to Jaipur for this Saturday.",
     "Shanivaar ko Delhi se Jaipur ke do ticket 3A mein book kar do",
     "शनिवार को दिल्ली से जयपुर के दो टिकट 3A में बुक कर दो"),
    ("seed-trv-002", TRAVEL, "book_cab",
     {"pickup": "Indiranagar", "drop": "airport", "pickup_time": "2026-11-13T05:30"}, [],
     ["kal", "fraction_idiom", "daypart"],
     "Book a cab from Indiranagar to the airport tomorrow at 5:30 am.",
     "Kal subah saade paanch baje Indiranagar se airport ke liye cab book karni hai",
     "कल सुबह साढ़े पाँच बजे इंदिरानगर से एयरपोर्ट के लिए कैब बुक करनी है"),
    ("seed-trv-003", TRAVEL, "search_flights",
     {"from_city": "Mumbai", "to_city": "Kolkata", "travel_date": "2026-11-20", "max_price_inr": "7500"}, [],
     ["absolute_date", "fraction_idiom"],
     "Find flights from Mumbai to Kolkata on 20 November under 7,500 rupees.",
     "20 November ko Mumbai se Kolkata ki flight dikhao, saade saat hazaar se kam mein",
     "20 नवंबर को मुंबई से कोलकाता की फ़्लाइट दिखाओ, साढ़े सात हज़ार से कम में"),
    ("seed-trv-004", TRAVEL, "book_train",
     {"from_city": "Pune", "to_city": "Hyderabad", "travel_date": "2026-11-14", "passengers": "4",
      "travel_class": "SL"}, [], ["parso"],
     "Book 4 sleeper tickets from Pune to Hyderabad for the day after tomorrow.",
     "Parso ke liye Pune se Hyderabad ke chaar sleeper ticket book karo",
     "परसों के लिए पुणे से हैदराबाद के चार स्लीपर टिकट बुक करो"),
    ("seed-trv-005", TRAVEL, "book_cab",
     {"pickup": "Koramangala", "drop": "Majestic", "pickup_time": "2026-11-12T21:15"}, [],
     ["fraction_idiom", "daypart"],
     "Book a cab from Koramangala to Majestic tonight at 9:15.",
     "Aaj raat sawa nau baje Koramangala se Majestic ki cab book kar do",
     "आज रात सवा नौ बजे कोरमंगला से मैजेस्टिक की कैब बुक कर दो"),
    ("seed-trv-006", TRAVEL, "book_cab", {"pickup": "Whitefield", "drop": "station"}, ["pickup_time"],
     ["bare_hour", "kal"],
     "I need a cab from Whitefield to the station tomorrow at 5.",
     "Kal 5 baje Whitefield se station ke liye cab chahiye",
     "कल 5 बजे व्हाइटफ़ील्ड से स्टेशन के लिए कैब चाहिए"),
    ("seed-trv-007", TRAVEL, "book_train",
     {"from_city": "Lucknow", "to_city": "Varanasi", "passengers": "3", "travel_class": "2A"}, ["travel_date"],
     ["missing_argument"],
     "Book 3 tickets from Lucknow to Varanasi in 2A.", "Lucknow se Varanasi ke teen ticket 2A mein book kar do",
     "लखनऊ से वाराणसी के तीन टिकट 2A में बुक कर दो"),
    ("seed-trv-008", TRAVEL, None, {}, [], ["negative", "lookalike_saath"],
     "Will you come to Goa with me?", "Mere saath Goa chaloge?", "मेरे साथ गोवा चलोगे?"),
    # ---- reminders
    ("seed-rem-001", REM, "set_alarm", {"time": "06:45"}, [], ["fraction_idiom", "daypart"],
     "Set an alarm for quarter to seven in the morning.", "Subah paune saat baje ka alarm laga do",
     "सुबह पौने सात बजे का अलार्म लगा दो"),
    ("seed-rem-002", REM, "set_reminder", {"at": "2026-11-13T18:00"}, [], ["kal", "daypart"],
     "Remind me tomorrow at 6 pm to call the doctor.",
     "Kal shaam 6 baje doctor ko call karne ka reminder laga dena",
     "कल शाम 6 बजे डॉक्टर को कॉल करने का रिमाइंडर लगा देना"),
    ("seed-rem-003", REM, "create_event", {"date": "2026-11-16", "start_time": "15:00", "duration": "PT1H30M"}, [],
     ["weekday", "fraction_idiom", "duration"],
     "Create a meeting on Monday at 3 pm for one and a half hours.",
     "Somvaar ko dopahar 3 baje dedh ghante ki meeting rakh do",
     "सोमवार को दोपहर 3 बजे डेढ़ घंटे की मीटिंग रख दो"),
    ("seed-rem-004", REM, "set_reminder", {"at": "2026-11-12T12:30"}, [], ["relative_time", "fraction_idiom"],
     "Remind me in two and a half hours to take my medicine.", "Dhai ghante baad dawai lene ka reminder laga do",
     "ढाई घंटे बाद दवाई लेने का रिमाइंडर लगा दो"),
    ("seed-rem-005", REM, "create_event", {"date": "2026-11-15", "start_time": "10:30", "duration": "PT45M"}, [],
     ["weekday", "fraction_idiom", "duration"],
     "Schedule a 45-minute yoga session this Sunday at 10:30 am.",
     "Ravivaar subah saade das baje 45 minute ka yoga session rakh do",
     "रविवार सुबह साढ़े दस बजे 45 मिनट का योग सेशन रख दो"),
    ("seed-rem-006", REM, "set_reminder", {}, ["at"], ["bare_hour"],
     "Remind me at 8 to call Mom.", "8 baje mummy ko call karne ka reminder laga do",
     "8 बजे मम्मी को कॉल करने का रिमाइंडर लगा दो"),
    ("seed-rem-007", REM, "create_event", {"date": "2026-11-14"}, ["start_time"], ["missing_argument", "weekday"],
     "Put Neha's birthday party on the calendar for Saturday.",
     "Shanivaar ko Neha ki birthday party calendar mein daal do",
     "शनिवार को नेहा की बर्थडे पार्टी कैलेंडर में डाल दो"),
    ("seed-rem-008", REM, None, {}, [], ["negative", "lookalike_ek_baar"],
     "Tell me once more, how does the alarm work?", "Mujhe ek baar phir se batao, alarm kaise kaam karta hai?",
     "मुझे एक बार फिर से बताओ, अलार्म कैसे काम करता है?"),
    # ---- shopping
    ("seed-shp-001", SHOP, "place_order", {"item": "salt", "quantity": "3"}, [], ["hindi_number_word"],
     "Order 3 packets of salt.", "Namak ke teen packet order kar do", "नमक के तीन पैकेट ऑर्डर कर दो"),
    ("seed-shp-002", SHOP, "place_order", {"item": "pressure cooker", "quantity": "1", "max_price_inr": "2250"}, [],
     ["fraction_idiom"],
     "Order one pressure cooker, not above 2,250 rupees.",
     "Ek pressure cooker order karo, sawa do hazaar se zyada ka nahi",
     "एक प्रेशर कुकर ऑर्डर करो, सवा दो हज़ार से ज़्यादा का नहीं"),
    ("seed-shp-003", SHOP, "set_price_alert", {"item": "laptop", "target_price_inr": "45000"}, [],
     ["hindi_number_word"],
     "Alert me when the laptop price drops to 45 thousand.",
     "Jab laptop ka daam paintaalis hazaar ho jaye to bata dena",
     "जब लैपटॉप का दाम पैंतालीस हज़ार हो जाए तो बता देना"),
    ("seed-shp-004", SHOP, "track_order", {"order_id": "OD-48213"}, [], ["id"],
     "Where is my order OD-48213?", "Mera order OD-48213 kahan tak pahuncha?",
     "मेरा ऑर्डर OD-48213 कहाँ तक पहुँचा?"),
    ("seed-shp-005", SHOP, "place_order", {"item": "notebook", "quantity": "25"}, [], ["hindi_number_word"],
     "Order 25 notebooks.", "Pachees notebook mangwa do", "पच्चीस नोटबुक मँगवा दो"),
    ("seed-shp-006", SHOP, "place_order", {"item": "pen"}, ["quantity"], ["approximate_pair"],
     "Order four or five pens.", "Chaar paanch pen order kar do", "चार-पाँच पेन ऑर्डर कर दो"),
    ("seed-shp-007", SHOP, "set_price_alert", {"item": "phone"}, ["target_price_inr"], ["missing_argument"],
     "Tell me when the phone gets cheaper.", "Phone sasta ho to bata dena", "फ़ोन सस्ता हो तो बता देना"),
    ("seed-shp-008", SHOP, None, {}, [], ["negative", "lookalike_do"],
     "I did not like this shirt, leave it.", "Yeh shirt mujhe pasand nahi aayi, rehne do",
     "यह शर्ट मुझे पसंद नहीं आई, रहने दो"),
    # ---- support
    ("seed-sup-001", SUP, "raise_ticket", {"category": "refund", "order_id": "OD-77120", "amount_inr": "1299"}, [],
     ["id"],
     "I want a refund of 1,299 rupees for order OD-77120.", "Order OD-77120 ka 1299 rupaye ka refund chahiye",
     "ऑर्डर OD-77120 का 1299 रुपये का रिफ़ंड चाहिए"),
    ("seed-sup-002", SUP, "request_callback", {"callback_time": "2026-11-13T11:00"}, [], ["kal", "daypart"],
     "Call me back tomorrow at 11 in the morning.", "Kal subah 11 baje mujhe callback kar dena",
     "कल सुबह 11 बजे मुझे कॉलबैक कर देना"),
    ("seed-sup-003", SUP, "check_refund_status", {"order_id": "OD-30455"}, [], ["id"],
     "What is the refund status of OD-30455?", "OD-30455 ka refund kab tak aayega?",
     "OD-30455 का रिफ़ंड कब तक आएगा?"),
    ("seed-sup-004", SUP, "raise_ticket", {"category": "billing", "amount_inr": "350"}, [], ["fraction_idiom"],
     "I was charged 350 rupees extra on my bill.", "Mere bill mein saade teen sau rupaye zyada kat gaye hain",
     "मेरे बिल में साढ़े तीन सौ रुपये ज़्यादा कट गए हैं"),
    ("seed-sup-005", SUP, "request_callback", {"callback_time": "2026-11-12T16:30"}, [],
     ["fraction_idiom", "daypart"],
     "Ask someone to call me today at 4:30 pm.", "Aaj shaam saade chaar baje kisi se call karwa do",
     "आज शाम साढ़े चार बजे किसी से कॉल करवा दो"),
    # seed-sup-006 is added below: its gold differs by variant.
    ("seed-sup-007", SUP, "raise_ticket", {"category": "refund"}, ["order_id"], ["missing_argument"],
     "I need a refund.", "Mujhe refund chahiye", "मुझे रिफ़ंड चाहिए"),
    ("seed-sup-008", SUP, None, {}, [], ["negative"],
     "Thanks, the issue is resolved now.", "Shukriya, ab problem theek ho gayi hai",
     "शुक्रिया, अब समस्या ठीक हो गई है"),
]

# "kal ki delivery": yesterday's or tomorrow's. English has to pick one, so the gold differs by variant.
KAL_ROW: dict[str, Any] = {
    "scenario": "seed-sup-006", "tools": SUP, "phenomena": ["kal", "variant_specific_gold"],
    "english": ("There is a problem with yesterday's delivery of order OD-51902.", "raise_ticket",
                {"category": "delivery", "order_id": "OD-51902", "incident_date": "2026-11-11"}, []),
    "roman": ("Order OD-51902 ki kal ki delivery ka issue hai", "raise_ticket",
              {"category": "delivery", "order_id": "OD-51902"}, ["incident_date"]),
    "devanagari": ("ऑर्डर OD-51902 की कल की डिलीवरी का इशू है", "raise_ticket",
                   {"category": "delivery", "order_id": "OD-51902"}, ["incident_date"]),
}

_DOMAIN = {"pay": "payments", "trv": "travel", "rem": "reminders", "shp": "shopping", "sup": "support"}
_SUFFIX = {"english": "en", "roman": "roman", "devanagari": "deva"}


def _item(scenario: str, tools: list[str], variant: str, utterance: str, tool: str | None, args: dict[str, str],
          clarify: list[str], phenomena: list[str], catalog: dict[str, dict[str, Any]]) -> Item:
    behavior = "abstain" if tool is None else ("clarify" if clarify else "call")
    gold: dict[str, Any] = {"tool": tool, "arguments": dict(args)}
    aliases = {k: ALIASES[v] for k, v in args.items() if v in ALIASES}
    if aliases:
        gold["aliases"] = aliases
    return {
        "schema_version": "1", "id": f"{scenario}-{_SUFFIX[variant]}", "scenario_id": scenario, "split": "seed",
        "domain": _DOMAIN[scenario.split("-")[1]], "variant": variant, "utterance": utterance, "now": NOW,
        "tools": [tool_for_item(t, catalog) for t in tools], "gold": gold, "phenomena": sorted(phenomena),
        "ambiguous": behavior == "clarify", "expected_behavior": behavior, "clarify_about": list(clarify),
        "provenance": "ai_drafted", "author_id": AUTHOR, "labels": [],
    }


def build_seed() -> list[Item]:
    catalog = load_tools()
    items: list[Item] = []
    for scenario, tools, tool, args, clarify, phen, en, roman, deva in ROWS:
        for variant, text in (("english", en), ("roman", roman), ("devanagari", deva)):
            items.append(_item(scenario, tools, variant, text, tool, args, clarify, phen, catalog))
    for variant in ("english", "roman", "devanagari"):
        text, tool, args, clarify = KAL_ROW[variant]
        items.append(_item(KAL_ROW["scenario"], KAL_ROW["tools"], variant, text, tool, args, clarify,
                           KAL_ROW["phenomena"], catalog))
    items.sort(key=lambda i: (i["scenario_id"], i["variant"]))
    return items
