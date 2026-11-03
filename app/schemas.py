"""Tool schemas and instructions used by the claim-processing agents."""
from __future__ import annotations

from typing import Any

from app.state import DOC_TYPES


def _nullable(value_type: str, description: str) -> dict[str, Any]:
    return {"type": [value_type, "null"], "description": description}


def _tool(name: str, description: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "description": description, "input_schema": schema}


SEGREGATOR_TOOL = _tool(
    "record_page_classification",
    "Record the document type of every page.",
    {
        "type": "object",
        "properties": {
            "classifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "document_type": {"type": "string", "enum": DOC_TYPES},
                        "reason": {"type": "string", "description": "One short sentence."},
                    },
                    "required": ["page", "document_type", "reason"],
                },
            }
        },
        "required": ["classifications"],
    },
)
SEGREGATOR_SYSTEM = """You classify pages of a health-insurance claim PDF.
Assign exactly one allowed document type to every page:
- claim_forms: insurance claim forms filled in by the patient or policy holder
- cheque_or_bank_details: cheque or bank account details
- identity_document: government ID, driver's licence, passport, or insurance ID card
- itemized_bill: itemized hospital, pharmacy, or clinic bill listing charges
- discharge_summary: hospital discharge summary
- prescription: doctor's prescription
- investigation_report: laboratory, pathology, radiology, or other test results
- cash_receipt: receipt proving a payment
- other: anything else, including consent forms, registration forms, letters, or questionnaires
Classify from the page's title and content, not incidental mentions. A continuation page gets
the same type as its document. Call the tool once with one entry per page."""


ID_FIELDS = {
    "patient_name": "Patient's full name",
    "date_of_birth": "Date of birth as YYYY-MM-DD",
    "gender": "Gender as printed",
    "id_type": "Kind of identity document",
    "id_number": "Number printed on the identity document",
    "id_issue_date": "Issue date as YYYY-MM-DD",
    "id_expiry_date": "Expiry date as YYYY-MM-DD",
    "address": "Address printed on the identity document",
    "contact_number": "Phone number",
    "email": "Email address",
    "insurance_company": "Insurance company name",
    "policy_number": "Insurance policy number",
    "group_number": "Insurance group number",
    "claim_reference": "Claim reference number",
}
ID_TOOL = _tool(
    "record_identity_information",
    "Record identity and policy information found in the provided pages.",
    {
        "type": "object",
        "properties": {
            key: _nullable("string", description) for key, description in ID_FIELDS.items()
        },
        "required": list(ID_FIELDS),
    },
)
ID_SYSTEM = """Extract identity and insurance-policy details from the provided identity-document
and/or claim-form pages. Copy values as printed, format dates as YYYY-MM-DD, use null if absent,
and never guess."""


DS_STRING_FIELDS = {
    "patient_name": "Patient name",
    "medical_record_number": "Medical record number",
    "date_of_birth": "Date of birth as YYYY-MM-DD",
    "hospital_name": "Hospital name",
    "admission_date": "Admission date as YYYY-MM-DD",
    "discharge_date": "Discharge date as YYYY-MM-DD",
    "diagnosis": "Admission or principal diagnosis",
    "attending_physician": "Attending physician name",
    "hospital_course": "Brief summary of the hospital course",
    "condition_at_discharge": "Condition at discharge",
    "follow_up": "Follow-up instructions",
}
DS_TOOL = _tool(
    "record_discharge_summary",
    "Record details of the hospital discharge summary.",
    {
        "type": "object",
        "properties": {
            **{
                key: _nullable("string", description)
                for key, description in DS_STRING_FIELDS.items()
            },
            "length_of_stay_days": _nullable("integer", "Length of stay in days if stated"),
            "discharge_medications": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Medicines prescribed at discharge",
            },
        },
        "required": [
            *DS_STRING_FIELDS,
            "length_of_stay_days",
            "discharge_medications",
        ],
    },
)
DS_SYSTEM = """Extract details from the provided hospital discharge-summary pages. Copy values
as printed, format dates as YYYY-MM-DD, use null or an empty list if absent, and never guess."""


BILL_TOOL = _tool(
    "record_itemized_bills",
    "Record every itemized bill found in the provided pages.",
    {
        "type": "object",
        "properties": {
            "bills": {
                "type": "array",
                "description": "One entry per separate bill; a bill may span multiple pages.",
                "items": {
                    "type": "object",
                    "properties": {
                        "bill_number": _nullable("string", "Bill or invoice number"),
                        "provider_name": _nullable("string", "Hospital, pharmacy, or clinic name"),
                        "bill_date": _nullable("string", "Bill date as YYYY-MM-DD"),
                        "patient_name": _nullable("string", "Patient name"),
                        "currency": _nullable("string", "ISO currency code if shown"),
                        "items": {
                            "type": "array",
                            "description": "Every charge line, in order; do not skip or merge lines.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": _nullable("string", "Line date as YYYY-MM-DD"),
                                    "description": {"type": "string"},
                                    "quantity": _nullable("number", "Quantity"),
                                    "unit_rate": _nullable("number", "Rate per unit"),
                                    "amount": {"type": "number", "description": "Line amount as printed"},
                                },
                                "required": [
                                    "date",
                                    "description",
                                    "quantity",
                                    "unit_rate",
                                    "amount",
                                ],
                            },
                        },
                        "subtotal": _nullable("number", "Subtotal printed on the bill"),
                        "discount": _nullable("number", "Discount amount, as a positive number"),
                        "tax": _nullable("number", "Tax amount printed on the bill"),
                        "total_amount_stated": _nullable(
                            "number",
                            "Grand total printed on the bill, before any insurance split",
                        ),
                    },
                    "required": [
                        "bill_number",
                        "provider_name",
                        "bill_date",
                        "patient_name",
                        "currency",
                        "items",
                        "subtotal",
                        "discount",
                        "tax",
                        "total_amount_stated",
                    ],
                },
            }
        },
        "required": ["bills"],
    },
)
BILL_SYSTEM = """Extract every charge line from the provided itemized-bill pages. Do not omit
or merge lines. Copy line amounts, subtotal, discount, tax, and total as printed; do not calculate
totals. Insurance payments and patient-responsibility lines are not charge items. Use null when
information is absent and never guess."""
