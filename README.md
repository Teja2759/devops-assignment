# Claim Processing Pipeline

FastAPI service that classifies the pages of a claim PDF with an LLM and routes them
through a LangGraph workflow to three extraction agents.

```
START -> Segregator (AI) -+-> ID Agent ------------------+
                          +-> Discharge Summary Agent ---+-> Aggregator -> END
                          +-> Itemized Bill Agent -------+
```

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```
Swagger UI: http://localhost:8000/docs

Or open http://localhost:8000, enter a claim ID, select a PDF, and click
**Upload and process PDF**. The extracted JSON appears on the page.

```bash
curl -X POST http://localhost:8000/api/process -F claim_id=CLM-1 -F file=@Final_1_.pdf
```

## How it works
1. **PDF -> pages**: `pypdf` extracts text per page.
2. **Segregator (LLM)**: sees every page (first 1500 chars) and labels each with one of the 9
   types (`claim_forms, cheque_or_bank_details, identity_document, itemized_bill,
   discharge_summary, prescription, investigation_report, cash_receipt, other`).
   If the LLM fails or returns an invalid label, a keyword fallback classifies that page.
3. **Routing**: the segregator records page numbers per agent in `page_routes`. Each agent
   sends only its assigned page text to the LLM:
   - ID Agent <- `identity_document` + `claim_forms` (policy details live on the claim form)
   - Discharge Summary Agent <- `discharge_summary`
   - Itemized Bill Agent <- `itemized_bill`
4. **Agents** run in parallel and use required structured tool schemas for their output.
   The bill agent extracts line items; **totals are calculated in code** using decimal
   arithmetic, compared with printed totals, and mismatches are returned as warnings.
5. **Aggregator** merges everything into the final JSON.

If LLM classification fails or omits a page, the keyword fallback classifies that page. The
response includes `segregation_method`, `page_routes`, `errors`, and `warnings` so fallback
classification and extraction/calculation issues are visible.

### Running without API credits

Set `LLM_MODE=offline` in `.env` to skip external model requests. The same three extraction
agents use local text-label and line-item patterns instead; the response reports
`processing_mode: "offline"` and warns that these results are best-effort and may be incomplete.
With `LLM_MODE=auto` (the default), the service uses the configured LLM and falls back locally
if a request fails, such as when API credits are exhausted. Set a valid API key and use
`LLM_MODE=auto` for AI classification and extraction.

## Response shape
```json
{
  "claim_id": "CLM-1",
  "total_pages": 17,
  "segregation_method": "llm",
  "document_classification": [{"page": 1, "document_type": "claim_forms", "reason": "..."}],
  "pages_by_document_type": {"claim_forms": [1], "identity_document": [3]},
  "page_routes": {"id_agent": [1, 3], "discharge_summary_agent": [4], "itemized_bill_agent": [9]},
  "extracted_data": {
    "identity": {}, "discharge_summary": {},
    "itemized_bill": {"bills": [], "items": [], "total_amount": 6329.3}
  },
  "errors": [],
  "warnings": []
}
```

## Video talking points
LangGraph state + fan-out/fan-in edges -> segregator tool schema and fallback -> page routing
(`AGENT_ROUTES` in `app/state.py`) -> extraction tool schemas -> bill total calculation and
validation -> aggregator.

## Deploy (Render/Railway)
Use the included `Dockerfile`; set `ANTHROPIC_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`.
Limitation: scanned PDFs without a text layer need OCR (not included).
