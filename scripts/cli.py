import typer
from rich import print

from src.workdrive.auth import token_status
from src.workdrive.inventory import crawl_incremental
from src.extraction.extract import run_extraction
from src.classify.heuristic import run_heuristics
from src.classify.llm import run_llm_pass
from src.sync.sync_templates import push_to_workdrive
from src.utils import write_csv, read_settings

app = typer.Typer(add_completion=False)

@app.command("auth")
def auth_status():
    print(token_status())

@app.command("crawl")
def crawl_run():
    crawl_incremental()

@app.command("extract")
def extract_run():
    run_extraction()

@app.command("classify")
def classify(stage: str = typer.Argument(..., help="heuristic|llm")):
    if stage == "heuristic":
        run_heuristics()
    elif stage == "llm":
        run_llm_pass()
    else:
        raise typer.BadParameter("Use 'heuristic' or 'llm'.")

@app.command("review")
def review(action: str = typer.Argument(..., help="export|import"),
           path: str = typer.Argument("data/inventory_labeled.csv")):
    if action == "export":
        write_csv(path)
    elif action == "import":
        from src.utils import import_corrected_csv
        import_corrected_csv(path)
    else:
        raise typer.BadParameter("Use 'export' or 'import'.")

@app.command("sync")
def sync_templates():
    push_to_workdrive()

@app.command("run")
def run_all(stage: str = typer.Argument("all")):
    crawl_incremental()
    run_extraction()
    run_heuristics()
    run_llm_pass()
    write_csv("data/inventory_labeled.csv")
    print("[green]Pipeline complete.[/green]")

if __name__ == "__main__":
    app()
