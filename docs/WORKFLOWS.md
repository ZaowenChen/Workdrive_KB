## Nightly job
1) crawl (incremental by modified_time)
2) extract new/changed files
3) heuristics → label
4) LLM on uncertain rows
5) export CSV snapshot for reviewers

## Weekly (or on-demand)
- Review in Streamlit or spreadsheet
- Import corrected CSV
- Sync to Data Templates
