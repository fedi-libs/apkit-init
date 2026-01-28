import subprocess
from pathlib import Path
from typing import Annotated, Optional

import questionary
import typer
from rich.console import Console
from rich.panel import Panel

from .api import fetch_templates
from .engine import apply_template

app = typer.Typer()
console = Console()

@app.command()
def main(dest: Annotated[Optional[str], typer.Argument(help="Target directory path")] = None):
    console.print(Panel.fit("🚀 [bold cyan]apkit-init[/bold cyan]"))

    try:
        templates = fetch_templates()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    choices = [
        questionary.Choice(title=f"{t['name']} by {t['author']} - {t['description']}", value=t) 
        for t in templates
    ]
    selected = questionary.select("Select a template:", choices=choices).ask()
    if not selected: 
        raise typer.Exit()

    template_url = selected["url"] or questionary.text("Enter custom Template Git URL:").ask()
    if not template_url:
        console.print("[red]No URL provided. Exiting.[/red]")
        raise typer.Exit(1)

    if not dest:
        dest = questionary.text("Target directory:", default="./my-fedi-app").ask()
    if not dest: 
        raise typer.Exit()
    
    actual_dest = dest
    if not actual_dest:
        actual_dest = questionary.text("Target directory:", default="./my-fedi-app").ask()
    
    if not actual_dest:
        raise typer.Exit()
    
    target_path = Path(actual_dest).resolve()
    project_name = questionary.text("Project name (slug):", default=target_path.name).ask()

    context = {"project_name": project_name}
    
    try:
        if target_path.exists() and any(target_path.iterdir()):
            if not questionary.confirm("Directory is not empty. Proceed?", default=False).ask():
                raise typer.Exit()

        with console.status("[bold yellow]Generating project..."):
            apply_template(template_url, target_path, context)
        
        if questionary.confirm("Initialize git repository?", default=True).ask():
            subprocess.run(["git", "init"], cwd=target_path, capture_output=True)

        console.print(f"\n[bold green]✨ Project {project_name} is ready![/bold green]")
        console.print(f"\n[bold]Next steps:[/bold]\n  cd {dest}\n  uv sync")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()