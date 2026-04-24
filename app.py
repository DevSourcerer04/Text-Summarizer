from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from textSummarizer.summarizer import get_summarizer, summarize_text

app = FastAPI(title="Text Summarizer API", version="1.0.0")
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to summarize")
    max_length: int = Field(110, ge=20, le=300)
    min_length: int = Field(30, ge=5, le=180)


class SummarizeResponse(BaseModel):
    summary: str


@app.on_event("startup")
def preload_model() -> None:
    # Preload model once during startup so user requests do not pay initialization cost.
    get_summarizer()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest) -> SummarizeResponse:
    if request.min_length >= request.max_length:
        raise HTTPException(status_code=400, detail="min_length must be less than max_length")

    try:
        summary = summarize_text(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            do_sample=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {exc}") from exc

    return SummarizeResponse(summary=summary)
