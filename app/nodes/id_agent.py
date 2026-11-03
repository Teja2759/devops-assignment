"""Extract identity and insurance-policy details from assigned pages."""
from app.llm import ask_tool, format_pages, is_offline_mode
from app.local_extraction import extract_identity_locally
from app.schemas import ID_SYSTEM, ID_TOOL
from app.state import ClaimState


def _fallback_warning(reason: str) -> str:
    return f"id_agent: {reason}; used local label matching, so results may be incomplete."


def id_agent_node(state: ClaimState) -> dict:
    page_numbers = state.get("page_routes", {}).get("id_agent", [])
    pages = [page for page in state["pages"] if page["page"] in page_numbers]
    if not pages:
        return {
            "extracted_data": {
                "identity": {"status": "no_pages_assigned", "pages_processed": []}
            }
        }
    try:
        if is_offline_mode():
            data = extract_identity_locally(pages)
            warning = _fallback_warning("offline mode is enabled")
        else:
            try:
                data = ask_tool(
                    ID_TOOL, ID_SYSTEM, format_pages(pages), tool_choice=ID_TOOL["name"]
                )
                warning = None
            except Exception as exc:
                data = extract_identity_locally(pages)
                warning = _fallback_warning(f"LLM unavailable ({type(exc).__name__})")
        data["pages_processed"] = page_numbers
        result = {"extracted_data": {"identity": data}}
        if warning:
            result["warnings"] = [warning]
        return result
    except Exception as exc:
        return {
            "extracted_data": {
                "identity": {"status": "failed", "pages_processed": page_numbers}
            },
            "errors": [f"id_agent: {exc}"],
        }
