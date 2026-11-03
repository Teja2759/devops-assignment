"""Combine classification and parallel agent outputs into the final response."""
from app.llm import is_offline_mode
from app.state import ClaimState


def aggregator_node(state: ClaimState) -> dict:
    extracted_data = state.get("extracted_data", {})
    local_fallback_used = any(
        value.get("extraction_method") is not None
        for value in extracted_data.values()
        if isinstance(value, dict)
    )
    processing_mode = (
        "offline"
        if is_offline_mode()
        else "fallback"
        if local_fallback_used or state.get("segregation_method") != "llm"
        else "llm"
    )
    result = {
        "claim_id": state["claim_id"],
        "total_pages": len(state["pages"]),
        "processing_mode": processing_mode,
        "segregation_method": state.get("segregation_method", "unknown"),
        "document_classification": state.get("classification", []),
        "pages_by_document_type": state.get("pages_by_document_type", {}),
        "page_routes": state.get("page_routes", {}),
        "extracted_data": state.get("extracted_data", {}),
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
    }
    return {"result": result}
