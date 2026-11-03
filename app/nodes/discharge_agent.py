"""Extract diagnosis, dates, and physician details from assigned pages."""
from app.llm import ask_tool, format_pages, is_offline_mode
from app.local_extraction import extract_discharge_locally
from app.schemas import DS_SYSTEM, DS_TOOL
from app.state import ClaimState


def _fallback_warning(reason: str) -> str:
    return (
        f"discharge_summary_agent: {reason}; used local label matching, "
        "so results may be incomplete."
    )


def discharge_agent_node(state: ClaimState) -> dict:
    page_numbers = state.get("page_routes", {}).get(
        "discharge_summary_agent", []
    )
    pages = [page for page in state["pages"] if page["page"] in page_numbers]
    if not pages:
        return {
            "extracted_data": {
                "discharge_summary": {
                    "status": "no_pages_assigned",
                    "pages_processed": [],
                }
            }
        }
    try:
        if is_offline_mode():
            data = extract_discharge_locally(pages)
            warning = _fallback_warning("offline mode is enabled")
        else:
            try:
                data = ask_tool(
                    DS_TOOL, DS_SYSTEM, format_pages(pages), tool_choice=DS_TOOL["name"]
                )
                warning = None
            except Exception as exc:
                data = extract_discharge_locally(pages)
                warning = _fallback_warning(f"LLM unavailable ({type(exc).__name__})")
        data["pages_processed"] = page_numbers
        result = {"extracted_data": {"discharge_summary": data}}
        if warning:
            result["warnings"] = [warning]
        return result
    except Exception as exc:
        return {
            "extracted_data": {
                "discharge_summary": {
                    "status": "failed",
                    "pages_processed": page_numbers,
                }
            },
            "errors": [f"discharge_summary_agent: {exc}"],
        }
