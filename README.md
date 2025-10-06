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

* Fill `.env` with Zoho OAuth Client ID/Secret and **refresh token**, your **teamfolder id**, and (optional) `OPENAI_API_KEY`.
* Edit `config/settings.yaml` to adjust picklists (doc_type, model, etc.) and template name.
* Edit `config/regex.yml` for heuristic patterns.

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

## License

MIT (or your preferred license)

```

