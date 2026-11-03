"""Keyword classifier used when LLM classification is unavailable or incomplete."""
from __future__ import annotations

import re

_RULES: list[tuple[str, list[str]]] = [
    ("cheque_or_bank_details", [r"cheque details", r"bank account details", r"cheque number"]),
    ("identity_document", [r"government id", r"identity card", r"\bid card\b", r"driver'?s? licen[cs]e", r"passport", r"aadhaar", r"national id"]),
    ("cash_receipt", [r"cash receipt", r"payment receipt"]),
    ("itemized_bill", [r"itemi[sz]ed", r"hospital bill", r"outpatient bill", r"\binvoice\b"]),
    ("discharge_summary", [r"discharge summary"]),
    ("prescription", [r"^\s*rx\b", r"\bprescription\b"]),
    ("investigation_report", [r"laboratory report", r"pathology", r"\bpanel\b", r"radiology", r"\bmri\b", r"ct scan report", r"x-ray report"]),
    ("claim_forms", [r"medical claim form", r"claim form", r"claim reference"]),
]

HEAD_CHARS = 400


def fallback_classify(text: str) -> tuple[str, str]:
    head = (text or "")[:HEAD_CHARS].lower()
    for doc_type, patterns in _RULES:
        for pattern in patterns:
            if re.search(pattern, head, flags=re.MULTILINE):
                return doc_type, f"keyword fallback: matched '{pattern}'"
    return "other", "keyword fallback: no keyword matched"
