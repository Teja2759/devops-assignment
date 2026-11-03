"""Shared LangGraph state and document-routing constants."""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

DOC_TYPES = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other",
]

AGENT_ROUTES: dict[str, list[str]] = {
    "id_agent": ["identity_document", "claim_forms"],
    "discharge_summary_agent": ["discharge_summary"],
    "itemized_bill_agent": ["itemized_bill"],
}

def merge_dicts(left: dict | None, right: dict | None) -> dict:
    """Merge parallel agent outputs, which write distinct extracted-data keys."""
    return {**(left or {}), **(right or {})}


class ClaimState(TypedDict, total=False):
    claim_id: str
    pages: list[dict[str, Any]]
    classification: list[dict[str, Any]]
    pages_by_document_type: dict[str, list[int]]
    page_routes: dict[str, list[int]]
    segregation_method: str
    extracted_data: Annotated[dict[str, Any], merge_dicts]
    errors: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]
    result: dict[str, Any]
