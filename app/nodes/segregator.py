"""Classify every PDF page and route only relevant page text to each agent."""
from __future__ import annotations

from app.fallback import fallback_classify
from app.llm import ask_tool, is_offline_mode
from app.schemas import SEGREGATOR_SYSTEM, SEGREGATOR_TOOL
from app.state import AGENT_ROUTES, DOC_TYPES, ClaimState

BATCH_SIZE = 25


def _classify_batch(batch: list[dict]) -> dict[int, dict]:
    prompt = "\n\n".join(
        f"=== PAGE {page['page']} ===\n{page['text'][:1500] or '[no extractable text]'}"
        for page in batch
    )
    result = ask_tool(
        SEGREGATOR_TOOL,
        SEGREGATOR_SYSTEM,
        prompt,
        tool_choice=SEGREGATOR_TOOL["name"],
    )
    rows = result.get("classifications")
    if not isinstance(rows, list):
        raise ValueError("classification tool returned no classifications list")
    classified: dict[int, dict] = {}
    for row in rows:
        page_number = row.get("page")
        if isinstance(page_number, int) and not isinstance(page_number, bool):
            classified[page_number] = row
    return classified


def segregator_node(state: ClaimState) -> dict:
    pages = state["pages"]
    warnings: list[str] = []
    llm_out: dict[int, dict] = {}
    fallback_pages: set[int] = set()

    if is_offline_mode():
        fallback_pages.update(page["page"] for page in pages)
        warnings.append("Segregator: offline mode; keyword classification was used.")
    else:
        for index in range(0, len(pages), BATCH_SIZE):
            batch = pages[index : index + BATCH_SIZE]
            try:
                batch_result = _classify_batch(batch)
                for page in batch:
                    row = batch_result.get(page["page"])
                    if row is None or row.get("document_type") not in DOC_TYPES:
                        fallback_pages.add(page["page"])
                    else:
                        llm_out[page["page"]] = row
            except Exception as exc:
                fallback_pages.update(page["page"] for page in batch)
                warnings.append(
                    f"Segregator: LLM unavailable ({type(exc).__name__}); "
                    f"keyword classification used for pages "
                    f"{batch[0]['page']}-{batch[-1]['page']}."
                )

        if fallback_pages and llm_out:
            warnings.append(
                f"Segregator: keyword classification used for {len(fallback_pages)} page(s) "
                "missing a valid LLM classification."
            )

    classification = []
    for page in pages:
        row = llm_out.get(page["page"])
        if row is None:
            doc_type, reason = fallback_classify(page["text"])
        else:
            doc_type, reason = row["document_type"], row.get("reason", "")
        classification.append(
            {"page": page["page"], "document_type": doc_type, "reason": reason}
        )

    pages_by_type: dict[str, list[int]] = {}
    type_by_page = {}
    for row in classification:
        pages_by_type.setdefault(row["document_type"], []).append(row["page"])
        type_by_page[row["page"]] = row["document_type"]

    page_routes = {
        agent: [
            page["page"]
            for page in pages
            if type_by_page[page["page"]] in allowed_types
        ]
        for agent, allowed_types in AGENT_ROUTES.items()
    }
    method = (
        "keyword_fallback"
        if len(fallback_pages) == len(pages)
        else "mixed"
        if fallback_pages
        else "llm"
    )
    return {
        "classification": classification,
        "pages_by_document_type": pages_by_type,
        "page_routes": page_routes,
        "segregation_method": method,
        "warnings": warnings,
    }
