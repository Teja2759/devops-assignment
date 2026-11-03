"""Extract itemized bills and calculate totals deterministically."""
from app.billing import compute_bill_totals
from app.llm import ask_tool, format_pages, is_offline_mode
from app.local_extraction import extract_bills_locally
from app.schemas import BILL_SYSTEM, BILL_TOOL
from app.state import ClaimState


def _fallback_warning(reason: str) -> str:
    return (
        f"itemized_bill_agent: {reason}; used local text patterns, "
        "so results may be incomplete."
    )


def itemized_bill_agent_node(state: ClaimState) -> dict:
    page_numbers = state.get("page_routes", {}).get("itemized_bill_agent", [])
    pages = [page for page in state["pages"] if page["page"] in page_numbers]
    if not pages:
        return {
            "extracted_data": {
                "itemized_bill": {
                    "status": "no_pages_assigned",
                    "pages_processed": [],
                    "bill_count": 0,
                    "total_item_count": 0,
                    "items": [],
                    "total_amount": 0.0,
                }
            }
        }
    try:
        if is_offline_mode():
            data = extract_bills_locally(pages)
            fallback_warning = _fallback_warning("offline mode is enabled")
        else:
            try:
                data = ask_tool(
                    BILL_TOOL, BILL_SYSTEM, format_pages(pages), tool_choice=BILL_TOOL["name"]
                )
                fallback_warning = None
            except Exception as exc:
                data = extract_bills_locally(pages)
                fallback_warning = _fallback_warning(f"LLM unavailable ({type(exc).__name__})")
        result = compute_bill_totals(data)
        result["pages_processed"] = page_numbers
        warnings = result["warnings"]
        if fallback_warning:
            warnings.insert(0, fallback_warning)
        return {
            "extracted_data": {"itemized_bill": result},
            "warnings": warnings,
        }
    except Exception as exc:
        return {
            "extracted_data": {
                "itemized_bill": {
                    "status": "failed",
                    "pages_processed": page_numbers,
                }
            },
            "errors": [f"itemized_bill_agent: {exc}"],
        }
