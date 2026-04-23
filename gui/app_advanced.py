"""Advanced Streamlit GUI for OpenAI Privacy Filter.

Funzionalita' aggiuntive rispetto ad app.py:
- modalita' output configurabile (tag / mask / label)
- highlight colorato delle entita' PII rilevate
- export JSON degli span
- supporto file PDF e DOCX
- batch upload: piu' file alla volta
- download di un archivio ZIP con i file redatti

Avvio:
    streamlit run gui/app_advanced.py
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import List

import streamlit as st

from file_loaders import ALL_EXTS, load_file
from redactor import (
    OUTPUT_MODES,
    OUTPUT_MODE_TAG,
    apply_redaction,
    highlight_html,
    load_pipeline,
    predict_spans,
    spans_to_json,
)

st.set_page_config(page_title="Privacy Filter GUI - Advanced", layout="wide")


@st.cache_resource(show_spinner="Carico il modello openai/privacy-filter...")
def _load():
    return load_pipeline()


def _sidebar() -> dict:
    st.sidebar.header("Impostazioni")
    mode = st.sidebar.selectbox(
        "Modalita' di output",
        options=list(OUTPUT_MODES),
        index=0,
        help="tag = <PERSON>, label = [PERSON], mask = ***",
    )
    show_highlight = st.sidebar.checkbox("Mostra highlight colorato", value=True)
    show_json = st.sidebar.checkbox("Mostra JSON degli span", value=False)
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Modello: `openai/privacy-filter` (Apache-2.0).  \n"
        "Tool di supporto alla redazione; non garantisce compliance."
    )
    return {
        "mode": mode,
        "show_highlight": show_highlight,
        "show_json": show_json,
    }


def _render_result(text: str, cfg: dict, tokenizer, model) -> tuple[str, list]:
    with st.spinner("Eseguo la redazione..."):
        spans = predict_spans(text, tokenizer, model)
        redacted = apply_redaction(text, spans, mode=cfg["mode"])

    cols = st.columns(2)
    with cols[0]:
        st.subheader("Originale")
        if cfg["show_highlight"]:
            st.markdown(highlight_html(text, spans), unsafe_allow_html=True)
        else:
            st.code(text or "(vuoto)", language="text")
    with cols[1]:
        st.subheader(f"Redatto ({cfg['mode']})")
        st.code(redacted or "(vuoto)", language="text")

    st.markdown(f"**Entita' rilevate:** {len(spans)}")
    if cfg["show_json"]:
        st.json(spans_to_json(spans))

    return redacted, spans


def _tab_text(cfg, tokenizer, model) -> None:
    text = st.text_area(
        "Testo da anonimizzare",
        height=220,
        placeholder="Incolla qui il testo contenente dati sensibili...",
    )
    if st.button("Anonimizza testo", type="primary", key="btn_text"):
        redacted, spans = _render_result(text, cfg, tokenizer, model)
        st.download_button(
            "Scarica .txt redatto",
            data=redacted.encode("utf-8"),
            file_name="redacted.txt",
            mime="text/plain",
        )
        st.download_button(
            "Scarica spans.json",
            data=json.dumps(spans_to_json(spans), indent=2, ensure_ascii=False).encode(
                "utf-8"
            ),
            file_name="spans.json",
            mime="application/json",
        )


def _tab_single_file(cfg, tokenizer, model) -> None:
    uploaded = st.file_uploader(
        "Carica un file",
        type=ALL_EXTS,
        accept_multiple_files=False,
        key="single",
    )
    if uploaded is None:
        return
    try:
        text, ext = load_file(uploaded.name, uploaded.read())
    except RuntimeError as exc:
        st.error(str(exc))
        return

    st.caption(f"File: **{uploaded.name}** ({ext}, {len(text)} caratteri)")
    if st.button("Anonimizza file", type="primary", key="btn_single"):
        redacted, spans = _render_result(text, cfg, tokenizer, model)
        base = uploaded.name.rsplit(".", 1)[0]
        st.download_button(
            "Scarica file redatto (.txt)",
            data=redacted.encode("utf-8"),
            file_name=f"{base}.redacted.txt",
            mime="text/plain",
        )
        st.download_button(
            "Scarica spans.json",
            data=json.dumps(spans_to_json(spans), indent=2, ensure_ascii=False).encode(
                "utf-8"
            ),
            file_name=f"{base}.spans.json",
            mime="application/json",
        )


def _tab_batch(cfg, tokenizer, model) -> None:
    files = st.file_uploader(
        "Carica piu' file",
        type=ALL_EXTS,
        accept_multiple_files=True,
        key="batch",
    )
    if not files:
        return
    if st.button(f"Anonimizza {len(files)} file", type="primary", key="btn_batch"):
        buf = io.BytesIO()
        progress = st.progress(0.0)
        summary: List[dict] = []
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, f in enumerate(files, start=1):
                try:
                    text, ext = load_file(f.name, f.read())
                    spans = predict_spans(text, tokenizer, model)
                    redacted = apply_redaction(text, spans, mode=cfg["mode"])
                    base = f.name.rsplit(".", 1)[0]
                    zf.writestr(f"{base}.redacted.txt", redacted)
                    zf.writestr(
                        f"{base}.spans.json",
                        json.dumps(spans_to_json(spans), indent=2, ensure_ascii=False),
                    )
                    summary.append(
                        {"file": f.name, "chars": len(text), "entities": len(spans)}
                    )
                except Exception as exc:
                    summary.append({"file": f.name, "error": str(exc)})
                progress.progress(idx / len(files))
        st.success("Batch completato.")
        st.dataframe(summary, use_container_width=True)
        st.download_button(
            "Scarica ZIP risultati",
            data=buf.getvalue(),
            file_name="redacted_batch.zip",
            mime="application/zip",
        )


def main() -> None:
    st.title("Privacy Filter GUI - Advanced")
    st.caption(
        "Interfaccia estesa per `openai/privacy-filter` (Apache-2.0): "
        "output mode, highlight, PDF/DOCX, batch, export JSON."
    )
    cfg = _sidebar()
    tokenizer, model = _load()

    tab_text, tab_file, tab_batch = st.tabs(["Testo", "File singolo", "Batch"])
    with tab_text:
        _tab_text(cfg, tokenizer, model)
    with tab_file:
        _tab_single_file(cfg, tokenizer, model)
    with tab_batch:
        _tab_batch(cfg, tokenizer, model)


if __name__ == "__main__":
    main()
