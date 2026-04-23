"""Core redaction module for Privacy Filter GUI.

Wraps the `openai/privacy-filter` token classifier and exposes high-level
helpers: span extraction, multiple output modes, JSON export.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

MODEL_ID = "openai/privacy-filter"

OUTPUT_MODE_TAG = "tag"          # <PERSON>, <EMAIL>, ...
OUTPUT_MODE_MASK = "mask"        # ***
OUTPUT_MODE_LABEL_MASK = "label" # [PERSON], [EMAIL], ...
OUTPUT_MODES = (OUTPUT_MODE_TAG, OUTPUT_MODE_MASK, OUTPUT_MODE_LABEL_MASK)


@dataclass
class Span:
    start: int
    end: int
    label: str
    text: str

    def to_dict(self) -> Dict:
        return asdict(self)


def load_pipeline(model_id: str = MODEL_ID):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForTokenClassification.from_pretrained(
        model_id, device_map="auto"
    )
    model.eval()
    return tokenizer, model


def _predict_spans(text: str, tokenizer, model) -> List[Span]:
    if not text or not text.strip():
        return []

    enc = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
        return_offsets_mapping=True,
    )
    offsets = enc.pop("offset_mapping")[0].tolist()
    enc = {k: v.to(model.device) for k, v in enc.items()}

    with torch.no_grad():
        logits = model(**enc).logits
    pred_ids = logits.argmax(dim=-1)[0].tolist()

    id2label = model.config.id2label
    spans: List[Span] = []
    cur_label = None
    cur_start = None
    cur_end = None

    for pid, (s, e) in zip(pred_ids, offsets):
        if s == 0 and e == 0:
            continue
        label = id2label.get(pid, "O")
        clean_label = label.split("-")[-1].upper() if label != "O" else "O"

        if clean_label == "O":
            if cur_label is not None:
                spans.append(
                    Span(cur_start, cur_end, cur_label, text[cur_start:cur_end])
                )
                cur_label = None
            continue

        if cur_label == clean_label and cur_end is not None and s <= cur_end + 1:
            cur_end = e
        else:
            if cur_label is not None:
                spans.append(
                    Span(cur_start, cur_end, cur_label, text[cur_start:cur_end])
                )
            cur_label = clean_label
            cur_start = s
            cur_end = e

    if cur_label is not None:
        spans.append(Span(cur_start, cur_end, cur_label, text[cur_start:cur_end]))

    return spans


def predict_spans(text: str, tokenizer, model, chunk_chars: int = 12000) -> List[Span]:
    """Predict PII spans, chunking long inputs by characters."""
    if len(text) <= chunk_chars:
        return _predict_spans(text, tokenizer, model)

    spans: List[Span] = []
    offset = 0
    while offset < len(text):
        piece = text[offset : offset + chunk_chars]
        for sp in _predict_spans(piece, tokenizer, model):
            spans.append(
                Span(sp.start + offset, sp.end + offset, sp.label, sp.text)
            )
        offset += chunk_chars
    return spans


def apply_redaction(text: str, spans: List[Span], mode: str = OUTPUT_MODE_TAG) -> str:
    if mode not in OUTPUT_MODES:
        raise ValueError(f"Unknown mode: {mode}")
    if not spans:
        return text

    ordered = sorted(spans, key=lambda s: s.start)
    out_parts: List[str] = []
    cursor = 0
    for sp in ordered:
        if sp.start < cursor:
            continue
        out_parts.append(text[cursor : sp.start])
        if mode == OUTPUT_MODE_TAG:
            out_parts.append(f"<{sp.label}>")
        elif mode == OUTPUT_MODE_LABEL_MASK:
            out_parts.append(f"[{sp.label}]")
        else:
            out_parts.append("*" * max(3, sp.end - sp.start))
        cursor = sp.end
    out_parts.append(text[cursor:])
    return "".join(out_parts)


def redact(
    text: str,
    tokenizer,
    model,
    mode: str = OUTPUT_MODE_TAG,
) -> Tuple[str, List[Span]]:
    spans = predict_spans(text, tokenizer, model)
    return apply_redaction(text, spans, mode=mode), spans


def spans_to_json(spans: List[Span]) -> List[Dict]:
    return [s.to_dict() for s in spans]


LABEL_COLORS = {
    "PERSON": "#f59e0b",
    "EMAIL": "#10b981",
    "PHONE": "#3b82f6",
    "ADDRESS": "#ef4444",
    "ORG": "#8b5cf6",
    "DATE": "#64748b",
    "ID": "#ec4899",
    "CREDIT_CARD": "#f43f5e",
    "IBAN": "#14b8a6",
    "URL": "#0ea5e9",
    "IP": "#a855f7",
}


def highlight_html(text: str, spans: List[Span]) -> str:
    if not spans:
        return f"<pre style='white-space:pre-wrap'>{_escape(text)}</pre>"
    ordered = sorted(spans, key=lambda s: s.start)
    out: List[str] = ["<pre style='white-space:pre-wrap;font-family:inherit'>"]
    cursor = 0
    for sp in ordered:
        if sp.start < cursor:
            continue
        out.append(_escape(text[cursor : sp.start]))
        color = LABEL_COLORS.get(sp.label, "#64748b")
        out.append(
            f"<mark style='background:{color};color:white;"
            f"padding:2px 4px;border-radius:4px;font-weight:600'>"
            f"{_escape(sp.text)}"
            f"<sub style='margin-left:4px;font-size:0.7em'>{sp.label}</sub>"
            f"</mark>"
        )
        cursor = sp.end
    out.append(_escape(text[cursor:]))
    out.append("</pre>")
    return "".join(out)


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
