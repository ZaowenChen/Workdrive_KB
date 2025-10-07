# WorkDrive Classifier (Inventory → Metadata → Review → Sync)

This repo builds a structured database of your Zoho WorkDrive files, auto-classifies them (heuristics + optional LLM), provides a manual review UI, and syncs corrected labels back to WorkDrive **Data Templates**.

**Key features**
- OAuth2 (authorization-code w/ refresh token)
- Paged inventory crawl with incremental sync
- Data Templates: create, attach, update
- Extraction: PDF/DOCX/XLSX → UTF-8 text excerpts
- Classification: regex heuristics + (optional) OpenAI
- Streamlit review app + CSV export/import
- SQLite for audit trail and reproducibility

## Quickstart

1) **Clone & install**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

2. **Configure**

* Fill `.env` with Zoho OAuth Client ID/Secret and **refresh token**, your **WorkDrive org id**, your **teamfolder id**, and (optional) `OPENAI_API_KEY`.
* Point `WORKDRIVE_API_BASE` at your custom domain if you use one (e.g. `https://workdrive.<company>.com/api/v1`), set `WORKDRIVE_APP_BASE` to the matching browser URL (e.g. `https://workdrive.<company>.com`) for quick links, and set `WORKDRIVE_ROOT_FOLDER_ID` to the folder id found after `/folders/` in the WorkDrive URL when you want to scope the crawl.
* Tune metadata taxonomies in `config/taxonomy.yaml` (Doc Type, Product Line, Models, Software/Hardware versions, etc.). These values drive the Streamlit review UI, CSV exports, and WorkDrive Data Template fields.
* Edit `config/settings.yaml` only if you need to change the WorkDrive Data Template name/description or adjust LLM options. Picklist contents now resolve automatically from `taxonomy.yaml`.
* Edit `config/regex.yml` for heuristic pre-label patterns.

3. **Initialize DB**

```bash
make db
```

4. **Crawl inventory**

```bash
make crawl
```

5. **Extract + classify**

```bash
make extract classify
# or a single command:
workdrive-cli run all
```

6. **Review and correct**

```bash
make review
# UI at http://localhost:8501
```

7. **Sync corrections to WorkDrive Data Templates**

```bash
make sync
```

8. **Export CSV**

```bash
make export
```

### Authentication (Zoho OAuth)

Use the **authorization-code** flow to obtain a `refresh_token` with offline access. Put it in `.env`. This app will auto-refresh `access_token` on expiry and cache it to `token.json`.

## CLI Cheatsheet

```
workdrive-cli auth status          # show token status
workdrive-cli crawl run            # inventory crawl (incremental)
workdrive-cli extract run          # download & extract excerpts
workdrive-cli classify heuristic   # regex-only pass
workdrive-cli classify llm         # LLM pass (only on low-confidence)
workdrive-cli review export        # write CSV for spreadsheet
workdrive-cli review import        # import corrected CSV
workdrive-cli sync templates       # push corrected labels to WorkDrive
workdrive-cli run all              # end-to-end (safe default flow)
```

## Notes

* OCR for scanned PDFs is **not** included by default. If needed, enable Tesseract and plug it into `extraction/extract.py` (hook provided).
* Legacy `.doc` requires conversion (LibreOffice headless). A hook is provided; set `ENABLE_DOC_CONVERSION` in `.env`.
* To shorten extraction time on large PDFs, tune `EXCERPT_PDF_MAX_PAGES` (default `0` = no limit). PowerPoint `.pptx` slides are extracted via `python-pptx`.
* Streamlit review enforces the Cobotiq labeling spec: Doc Type → Product Line → Model → Software/Hardware versions (with “Other” text boxes) → Subsystem → Audience → Priority → Lifecycle → Confidentiality → Keywords. Keywords become mandatory when Doc Type is **Other**.

## License

MIT (or your preferred license)

```
