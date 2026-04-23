# Privacy Filter GUI

Interfaccia grafica (Streamlit) non ufficiale per il modello
[`openai/privacy-filter`](https://github.com/openai/privacy-filter),
rilasciato con licenza **Apache 2.0**.

Due versioni disponibili:

- **`app.py`** - GUI minimale (solo testo e file testuali).
- **`app_advanced.py`** - GUI estesa (consigliata), con:
  - modalita' output configurabile: `tag` / `label` / `mask`;
  - highlight colorato delle entita' rilevate;
  - export JSON degli span con posizione e label;
  - supporto file PDF e DOCX;
  - batch upload di piu' file, risultati in ZIP;
  - download singolo file redatto + `.spans.json`.

> Questo tool e' un supporto alla redazione dei dati sensibili.
> Non garantisce da solo piena anonimizzazione o compliance normativa (GDPR, ecc.).

## Formati file supportati

`.txt`, `.csv`, `.json`, `.log`, `.md`, `.xml`, `.html`, `.yaml`, `.yml`,
`.pdf` (via `pypdf`), `.docx` (via `python-docx`).

## Requisiti

- Python 3.10+
- GPU consigliata (CPU funziona ma e' piu' lenta)
- ~2 GB di spazio per la cache del modello HuggingFace

## Installazione locale

```bash
git clone https://github.com/marcko80/privacy-filter-GUI.git
cd privacy-filter-GUI
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r gui/requirements.txt
```

## Avvio

Versione avanzata (consigliata):

```bash
streamlit run gui/app_advanced.py
```

Versione base:

```bash
streamlit run gui/app.py
```

La GUI si apre su http://localhost:8501.

## Avvio con Docker

```bash
docker compose up -d --build
```

Il volume `hf-cache` conserva il modello scaricato tra i riavvii.

## Deploy dietro Nginx

Vedi [`deploy/nginx.conf.example`](../deploy/nginx.conf.example) per un
esempio di reverse proxy con HTTPS e supporto WebSocket per Streamlit.

## Moduli

- `redactor.py` - logica core: caricamento modello, predizione span,
  modalita' di output, highlight HTML.
- `file_loaders.py` - caricamento di file testuali, PDF e DOCX.
- `app.py` / `app_advanced.py` - applicazioni Streamlit.

## Licenza

Questo repository e' un fork di `openai/privacy-filter` ed eredita la licenza
**Apache 2.0**. Vedi il file [`LICENSE`](../LICENSE).

Modifiche rispetto all'upstream:

- aggiunta della cartella `gui/` con applicazioni Streamlit e moduli di supporto;
- aggiunta di `Dockerfile`, `docker-compose.yml`, `.streamlit/config.toml`;
- aggiunta di `deploy/nginx.conf.example`;
- aggiunta del workflow `.github/workflows/lint.yml`.

Questo progetto non e' affiliato a OpenAI.
