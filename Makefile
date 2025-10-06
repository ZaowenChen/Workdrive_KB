.PHONY: db crawl extract classify review sync export

VENV=.venv
PY=$(VENV)/bin/python

PY_RUN=PYTHONPATH=. $(PY)

db:
	$(PY) -c "from src.db import init_db; init_db()"

crawl:
	$(PY_RUN) scripts/cli.py crawl

extract:
	$(PY_RUN) scripts/cli.py extract

classify:
	$(PY_RUN) scripts/cli.py classify heuristic
	$(PY_RUN) scripts/cli.py classify llm

review:
	$(PY_RUN) -m streamlit run src/apps/streamlit_app.py

sync:
	$(PY_RUN) scripts/cli.py sync

export:
	$(PY_RUN) scripts/cli.py review export
