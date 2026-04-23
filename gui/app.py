"""Streamlit GUI for OpenAI Privacy Filter.

Front-end per caricare testo o file e ottenere una versione anonimizzata
usando il modello `openai/privacy-filter` (Apache-2.0).

Esecuzione:
    pip install -r gui/requirements.txt
    streamlit run gui/app.py
"""

from __future__ import annotations

from typing import List, Tuple

import streamlit as st
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

MODEL_ID = "openai/privacy-filter"
SUPPORTED_EXT = ["txt", "csv", "json", "log", "md"]


@st.cache_resource(show_spinner="Carico il modello openai/privacy-filter...")
def load_model() -> Tuple[AutoTokenizer, AutoModelForTokenClassification]:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_ID, device_map="auto"
    )
    model.eval()
    return tokenizer, model


def _chunk_text(text: str, tokenizer, max_tokens: int = 2048) -> List[str]:
    if not text:
        return []
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    if len(ids) <= max_tokens:
        return [text]
    chunks = []
    for i in range(0, len(ids), max_tokens):
        piece_ids = ids[i : i + max_tokens]
        chunks.append(tokenizer.decode(piece_ids, skip_special_tokens=True))
    return chunks


def redact_text(text: str, tokenizer, model) -> str:
    if not text or not text.strip():
        return ""

    device = model.device
    out_parts: List[str] = []

    for chunk in _chunk_text(text, tokenizer):
        inputs = tokenizer(
            chunk, return_tensors="pt", truncation=True, max_length=4096
        ).to(device)

        with torch.no_grad():
            logits = model(**inputs).logits

        pred_ids = logits.argmax(dim=-1)[0].tolist()
        input_ids = inputs["input_ids"][0].tolist()
        tokens = tokenizer.convert_ids_to_tokens(input_ids)
        id2label = model.config.id2label

        redacted_tokens: List[str] = []
        prev_label = "O"
        for tok, pid in zip(tokens, pred_ids):
            label = id2label.get(pid, "O")
            if tok in tokenizer.all_special_tokens:
                continue
            if label != "O":
                clean_label = label.split("-")[-1].upper()
                if clean_label != prev_label:
                    redacted_tokens.append(f" <{clean_label}>")
                prev_label = clean_label
            else:
                prev_label = "O"
                redacted_tokens.append(tokenizer.convert_tokens_to_string([tok]))

        out_parts.append("".join(redacted_tokens))

    return "".join(out_parts).strip()


def main() -> None:
    st.set_page_config(page_title="Privacy Filter GUI", layout="wide")
    st.title("Privacy Filter GUI")
    st.caption(
        "Interfaccia grafica non ufficiale per il modello "
        "`openai/privacy-filter` (Apache-2.0)."
    )

    with st.sidebar:
        st.header("Info")
        st.markdown(
            "- Modello: **openai/privacy-filter**\n"
            "- Uso: rilevazione e mascheratura di PII\n"
            "- Strumento di supporto: non garantisce da solo "
            "piena anonimizzazione o compliance."
        )

    tokenizer, model = load_model()

    tab_text, tab_file = st.tabs(["Testo", "File"])

    with tab_text:
        input_text = st.text_area(
            "Testo da anonimizzare",
            height=240,
            placeholder="Incolla qui il testo con dati sensibili...",
        )
        if st.button("Anonimizza testo", type="primary"):
            with st.spinner("Eseguo la redazione..."):
                redacted = redact_text(input_text, tokenizer, model)
            st.subheader("Risultato")
            st.code(redacted or "(vuoto)", language="text")
            st.download_button(
                "Scarica .txt",
                data=redacted.encode("utf-8"),
                file_name="redacted.txt",
                mime="text/plain",
            )

    with tab_file:
        uploaded = st.file_uploader(
            "Carica un file di testo",
            type=SUPPORTED_EXT,
            accept_multiple_files=False,
        )
        if uploaded is not None:
            raw_bytes = uploaded.read()
            try:
                raw = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raw = raw_bytes.decode("latin-1", errors="ignore")

            st.text_area("Contenuto originale", raw, height=220)

            if st.button("Anonimizza file", key="btn_file", type="primary"):
                with st.spinner("Eseguo la redazione sul file..."):
                    redacted = redact_text(raw, tokenizer, model)

                st.subheader("Risultato")
                st.code(redacted or "(vuoto)", language="text")

                base = uploaded.name.rsplit(".", 1)[0]
                ext = uploaded.name.rsplit(".", 1)[-1]
                out_name = f"{base}.redacted.{ext}"
                st.download_button(
                    "Scarica file anonimizzato",
                    data=redacted.encode("utf-8"),
                    file_name=out_name,
                    mime="text/plain",
                )


if __name__ == "__main__":
    main()
