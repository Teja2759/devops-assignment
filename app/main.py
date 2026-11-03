import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.graph import claim_graph
from app.pdf_utils import extract_pages

app = FastAPI(
    title="Claim Processing Pipeline",
    version="1.0.0",
    description="Classify claim PDF pages and extract identity, discharge, and bill data.",
)

health_router = APIRouter(prefix="/health")


@health_router.get("/", response_model=dict[str, str])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(health_router)

MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024


@app.get("/", include_in_schema=False)
async def upload_page() -> FileResponse:
    return FileResponse(Path(__file__).with_name("index.html"))


@app.post("/api/process", response_model=dict[str, Any])
async def process_pdf_claim(
    claim_id: Annotated[str, Form(min_length=1, max_length=128)],
    file: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    data = await file.read()
    if not data:
        raise HTTPException(400, "Uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File too large.")
    if not data.lstrip().startswith(b"%PDF"):
        raise HTTPException(400, "Uploaded file is not a PDF.")
    try:
        pages = extract_pages(data)
    except Exception as exc:
        raise HTTPException(400, f"Could not read PDF: {exc}")
    if not pages:
        raise HTTPException(400, "PDF has no pages.")

    final = await claim_graph.ainvoke({"claim_id": claim_id, "pages": pages, "errors": []})
    return final["result"]
