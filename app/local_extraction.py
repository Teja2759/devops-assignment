"""Best-effort text-pattern extraction for demos without an available LLM."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def _text(pages: list[dict[str, Any]]) -> str:
    return "\n".join(str(page.get("text") or "") for page in pages)


def _field(text: str, labels: str) -> str | None:
    match = re.search(
        rf"(?im)^\s*(?:{labels})\s*[:#-]\s*(.*?)\s*$",
        text,
    )
    value = match.group(1).strip(" \t|,;") if match else ""
    return value or None


def _date(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return value


def extract_identity_locally(pages: list[dict[str, Any]]) -> dict[str, Any]:
    text = _text(pages)
    fields = {
        "patient_name": r"(?:patient'?s?\s+name|name\s+of\s+patient|patient)",
        "date_of_birth": r"(?:date\s+of\s+birth|birth\s+date|dob)",
        "gender": r"(?:gender|sex)",
        "id_number": r"(?:id\s*(?:number|no\.?)|identity\s*(?:number|no\.?)|aadhaar\s*(?:number|no\.?)|passport\s*(?:number|no\.?))",
        "id_type": r"(?:id\s+type|identity\s+type)",
        "id_issue_date": r"(?:issue\s+date|date\s+of\s+issue)",
        "id_expiry_date": r"(?:expiry\s+date|expiration\s+date|date\s+of\s+expiry)",
        "address": r"(?:permanent\s+address|residential\s+address|address)",
        "contact_number": r"(?:contact\s+(?:number|no\.?)|phone(?:\s+number)?|mobile(?:\s+number)?)",
        "email": r"(?:e-?mail(?:\s+address)?)",
        "insurance_company": r"(?:insurance\s+company|insurer)",
        "policy_number": r"(?:policy\s*(?:number|no\.?))",
        "group_number": r"(?:group\s*(?:number|no\.?))",
        "claim_reference": r"(?:claim\s*(?:reference|ref|number|no\.?))",
    }
    data = {key: _field(text, labels) for key, labels in fields.items()}
    for key in ("date_of_birth", "id_issue_date", "id_expiry_date"):
        data[key] = _date(data[key])
    return {
        **data,
        "status": "local_fallback",
        "extraction_method": "label_matching",
        "pages_processed": [page["page"] for page in pages],
    }


def extract_discharge_locally(pages: list[dict[str, Any]]) -> dict[str, Any]:
    text = _text(pages)
    fields = {
        "patient_name": r"(?:patient'?s?\s+name|name\s+of\s+patient|patient)",
        "medical_record_number": r"(?:medical\s+record\s+(?:number|no\.?)|mrn)",
        "date_of_birth": r"(?:date\s+of\s+birth|birth\s+date|dob)",
        "hospital_name": r"(?:hospital\s+name|hospital)",
        "admission_date": r"(?:admission\s+date|date\s+of\s+admission|admitted\s+on)",
        "discharge_date": r"(?:discharge\s+date|date\s+of\s+discharge|discharged\s+on)",
        "diagnosis": r"(?:principal\s+diagnosis|final\s+diagnosis|diagnosis)",
        "attending_physician": r"(?:attending\s+physician|attending\s+doctor|consultant)",
        "hospital_course": r"(?:hospital\s+course|clinical\s+course)",
        "condition_at_discharge": r"(?:condition\s+at\s+discharge|discharge\s+condition)",
        "follow_up": r"(?:follow[- ]?up(?:\s+instructions)?|review\s+after)",
    }
    data = {key: _field(text, labels) for key, labels in fields.items()}
    for key in ("date_of_birth", "admission_date", "discharge_date"):
        data[key] = _date(data[key])
    medication_text = _field(text, r"(?:discharge\s+medications|medications\s+on\s+discharge)")
    medications = (
        [part.strip() for part in re.split(r"[,;]", medication_text) if part.strip()]
        if medication_text
        else []
    )
    return {
        **data,
        "length_of_stay_days": None,
        "discharge_medications": medications,
        "status": "local_fallback",
        "extraction_method": "label_matching",
        "pages_processed": [page["page"] for page in pages],
    }


def extract_bills_locally(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract clearly labeled totals and simple trailing-amount bill rows."""
    bills: list[dict[str, Any]] = []
    excluded = re.compile(r"\b(subtotal|sub-total|grand total|total|discount|tax|gst|vat)\b", re.I)
    for page in pages:
        lines = [line.strip() for line in str(page.get("text") or "").splitlines() if line.strip()]
        if not lines:
            continue
        amounts: dict[str, float | None] = {
            "subtotal": None,
            "discount": None,
            "tax": None,
            "total_amount_stated": None,
        }
        items = []
        for line in lines:
            value_match = re.search(r"(-?\d[\d,]*(?:\.\d{1,2})?)\s*$", line)
            if not value_match:
                continue
            value = float(value_match.group(1).replace(",", ""))
            label = line[: value_match.start()].strip(" :-")
            if re.search(r"\b(subtotal|sub-total)\b", label, re.I):
                amounts["subtotal"] = value
            elif re.search(r"\b(discount)\b", label, re.I):
                amounts["discount"] = value
            elif re.search(r"\b(tax|gst|vat)\b", label, re.I):
                amounts["tax"] = value
            elif re.search(r"\b(grand total|total due|net payable|total amount)\b", label, re.I):
                amounts["total_amount_stated"] = value
            elif label and not excluded.search(label):
                items.append(
                    {
                        "date": None,
                        "description": label,
                        "quantity": None,
                        "unit_rate": None,
                        "amount": value,
                    }
                )
        if items or any(value is not None for value in amounts.values()):
            bills.append(
                {
                    "bill_number": None,
                    "provider_name": None,
                    "bill_date": None,
                    "patient_name": None,
                    "currency": None,
                    "items": items,
                    **amounts,
                }
            )
    return {"bills": bills}
