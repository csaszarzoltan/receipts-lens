"""Tax category catalogue and deterministic rules."""

TAX_CATEGORIES = {
    "US": [
        {"id": i, "label": l, "locale": "US", "line": line}
        for i, l, line in [
            ("advertising", "Advertising", "Line 8"),
            ("car_truck", "Transportation - Car/Truck", "Line 9"),
            ("commissions", "Commissions and Fees", "Line 10"),
            ("contract", "Contract Labor", "Line 11"),
            ("depreciation", "Depreciation and Section 179", "Line 13"),
            ("insurance", "Business Insurance", "Line 15"),
            ("interest", "Business Interest", "Line 16"),
            ("professional", "Legal and Professional Services", "Line 17"),
            ("office", "Office Supplies", "Line 18"),
            ("rent", "Rent or Lease", "Line 20"),
            ("repairs", "Repairs and Maintenance", "Line 21"),
            ("supplies", "Supplies", "Line 22"),
            ("travel", "Travel - Lodging", "Line 24a"),
            ("meals", "Meals and Entertainment - 50%", "Line 24b"),
        ]
    ],
    "HU": [
        {
            "id": f"afa_{x}",
            "label": f"{x}% AFA" if x else "0% AFA / AAM",
            "locale": "HU",
            "line": f"{x}%",
        }
        for x in (27, 18, 5, 0)
    ],
}
_TAX_RULES = [
    ("uber", "Transportation - Car/Truck", "US"),
    ("lyft", "Transportation - Car/Truck", "US"),
    ("shell", "Transportation - Car/Truck", "US"),
    ("starbucks", "Meals and Entertainment - 50%", "US"),
    ("mcdonald", "Meals and Entertainment - 50%", "US"),
    ("office depot", "Office Supplies", "US"),
    ("staples", "Office Supplies", "US"),
    ("marriott", "Travel - Lodging", "US"),
    ("hilton", "Travel - Lodging", "US"),
    ("google ads", "Advertising", "US"),
    ("upwork", "Contract Labor", "US"),
    ("accountant", "Legal and Professional Services", "US"),
    ("wework", "Rent or Lease", "US"),
    ("repair", "Repairs and Maintenance", "US"),
    ("aldi", "27% AFA", "HU"),
    ("lidl", "27% AFA", "HU"),
    ("etterem", "18% AFA", "HU"),
    ("szallas", "18% AFA", "HU"),
    ("spar", "5% AFA", "HU"),
    ("gyogyszertar", "0% AFA / AAM", "HU"),
]


def labels(locale: str) -> set[str]:
    return {x["label"] for x in TAX_CATEGORIES.get(locale.upper(), [])}
