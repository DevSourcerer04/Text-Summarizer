from __future__ import annotations

from functools import lru_cache
import os
import re

import torch
from transformers import pipeline

MODEL_NAME = os.getenv("SUMMARIZER_MODEL", "sshleifer/distilbart-cnn-6-6")
MAX_INPUT_CHARS = int(os.getenv("SUMMARIZER_MAX_INPUT_CHARS", "2800"))
ALLOW_MPS = os.getenv("SUMMARIZER_ALLOW_MPS", "0") == "1"
CLIPPED_TAIL_WORDS = {
    "as",
    "to",
    "of",
    "for",
    "with",
    "by",
    "in",
    "on",
    "at",
    "from",
    "and",
    "or",
    "but",
    "before",
    "after",
    "while",
    "because",
    "during",
    "since",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "has",
    "have",
    "had",
}


def _resolve_device():
    if torch.cuda.is_available():
        return 0
    # MPS still misses some operators for certain seq2seq models; keep CPU default.
    if ALLOW_MPS and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return -1


@lru_cache(maxsize=1)
def get_summarizer(device_override=None):
    device = device_override if device_override is not None else _resolve_device()
    return pipeline("summarization", model=MODEL_NAME, tokenizer=MODEL_NAME, device=device)


def _finalize_summary(summary: str) -> str:
    cleaned = " ".join(summary.strip().split())
    cleaned = re.sub(r"\s+([.,!?;:])", r"\1", cleaned)
    if not cleaned:
        return cleaned

    if cleaned[-1] in ".!?":
        return cleaned

    sentence_end_positions = [cleaned.rfind("."), cleaned.rfind("!"), cleaned.rfind("?")]
    last_end = max(sentence_end_positions)
    if last_end >= int(len(cleaned) * 0.5):
        return cleaned[: last_end + 1].strip()

    return f"{cleaned}."


def _looks_clipped(summary: str) -> bool:
    stripped = summary.strip()
    if not stripped:
        return False
    if stripped.endswith(("...", "…")):
        return True

    last_word = re.sub(r"[^\w']+$", "", stripped).split()[-1].lower()
    return last_word in CLIPPED_TAIL_WORDS


def _trim_trailing_fragment(summary: str) -> str:
    stripped = summary.strip()
    core = stripped.rstrip(".!?")
    split_idx = max(core.rfind(","), core.rfind(";"), core.rfind(":"))
    if split_idx >= int(len(core) * 0.5):
        trimmed = core[:split_idx].rstrip()
        if trimmed:
            return f"{trimmed}."

    words = core.split()
    if len(words) > 10:
        return f"{' '.join(words[:-4]).rstrip(',;:')}."
    return stripped


def _generate_summary(summarizer, text: str, max_length: int, min_length: int, do_sample: bool) -> str:
    output = summarizer(
        text,
        max_length=max_length,
        min_length=min_length,
        do_sample=do_sample,
        num_beams=4,
        early_stopping=True,
        no_repeat_ngram_size=3,
    )
    return output[0]["summary_text"]


def summarize_text(
    text: str,
    max_length: int = 110,
    min_length: int = 30,
    do_sample: bool = False,
) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Text input cannot be empty.")
    if len(cleaned) > MAX_INPUT_CHARS:
        raise ValueError(f"Input text is too long. Please keep it under {MAX_INPUT_CHARS} characters for fast results.")

    summarizer = get_summarizer()
    try:
        summary = _generate_summary(
            summarizer=summarizer,
            text=cleaned,
            max_length=max_length,
            min_length=min_length,
            do_sample=do_sample,
        )
    except Exception as exc:
        # If an MPS op is missing, retry once on CPU.
        if "MPS" not in str(exc).upper():
            raise
        summarizer = get_summarizer(device_override=-1)
        summary = _generate_summary(
            summarizer=summarizer,
            text=cleaned,
            max_length=max_length,
            min_length=min_length,
            do_sample=do_sample,
        )

    finalized = _finalize_summary(summary)
    if _looks_clipped(finalized):
        retry_max_length = min(max_length + 32, 256)
        if retry_max_length > max_length:
            retry_summary = _generate_summary(
                summarizer=summarizer,
                text=cleaned,
                max_length=retry_max_length,
                min_length=min_length,
                do_sample=do_sample,
            )
            retry_finalized = _finalize_summary(retry_summary)
            if not _looks_clipped(retry_finalized):
                return retry_finalized
            finalized = retry_finalized

    if _looks_clipped(finalized):
        finalized = _trim_trailing_fragment(finalized)
    return finalized
