"""Eight one-tap examples. Every name, amount and date is made up."""
from __future__ import annotations

#: all examples use the same stated 'now', shown in the form: Thursday 12 November 2026, 10:00
NOW = ("2026-11-12", "10:00")
EXAMPLES: tuple[tuple[str, str], ...] = (
    ("Payment request", "Ramesh ko kal 5 baje dhai lakh rupaye bhej dena"),
    ("Collections call", "Sir, aapki EMI ke saade teen hazaar rupaye parso tak jama kar dijiye"),
    ("Reminder", "aaj 2 bje doctor ko call krungi, yaad dila dena"),
    ("Train booking", "agle shukravaar ki train mein do ticket book kar do"),
    ("COD order", "COD order hai, paune do hazaar rupaye delivery par dene honge"),
    ("Salary", "meri salary dedh lakh rupaye mahina hai"),
    ("How long", "meeting dhai ghante chalegi"),
    ("देवनागरी", "सुरेश को कल शाम साढ़े पाँच बजे ढाई हज़ार रुपये भेज देना"),
)
