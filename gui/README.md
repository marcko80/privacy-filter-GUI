# Privacy Filter GUI

Interfaccia grafica (Streamlit) non ufficiale per il modello
[`openai/privacy-filter`](https://github.com/openai/privacy-filter),
rilasciato con licenza **Apache 2.0**.

Permette di:

- incollare testo e ottenerne una versione anonimizzata;
- caricare un file (`.txt`, `.csv`, `.json`, `.log`, `.md`) e scaricarlo anonimizzato;
- vedere le entita' PII mascherate con tag tipo `<PERSON>`, `<EMAIL>`, `<PHONE>`, ecc.

> Questo tool e' un supporto alla redazione dei dati sensibili.
> Non garantisce da solo piena anonimizzazione o compliance normativa (GDPR, ecc.).

## Requisiti

- Python 3.10+
- GPU consigliata (CPU funziona ma e' piu' lenta)

## Installazione

```bash
git clone https://github.com/marcko80/privacy-filter-GUI.git
cd privacy-filter-GUI
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r gui/requirements.txt
```

## Avvio

```bash
streamlit run gui/app.py
```

La GUI si apre su http://localhost:8501.

## Uso

1. Apri la tab **Testo** o **File**.
2. Incolla il testo oppure carica un file supportato.
3. Clicca **Anonimizza**.
4. Scarica l'output redatto.

## Licenza

Questo repository e' un fork di `openai/privacy-filter` ed eredita la licenza
**Apache 2.0**. Vedi il file [`LICENSE`](../LICENSE).

Modifiche rispetto all'upstream:

- aggiunta della cartella `gui/` con applicazione Streamlit (`app.py`,
  `requirements.txt`, `README.md`).

Questo progetto non e' affiliato a OpenAI.
