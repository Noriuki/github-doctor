"""CLI interface for GitHub Doctor."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config import get_github_client
from app.application.analyze_repository_use_case import AnalyzeRepositoryUseCase
from app.application.repository_analysis.report_formatter import report_to_markdown

app = typer.Typer(
    name="github-doctor",
    help="Analyze GitHub repositories and generate health reports.",
)
console = Console()


def _run_async(coro):
    """Run async use case from sync CLI."""
    return asyncio.run(coro)


@app.command()
def analyze(
    repo: str = typer.Argument(..., help="Repository in form owner/repo (e.g. octocat/Hello-World)"),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Output full report as Markdown"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write Markdown report to file"),
) -> None:
    """Analyze a GitHub repository and print the health report."""
    if "/" not in repo:
        console.print("[red]Repository must be in form owner/repo[/red]")
        raise typer.Exit(1)
    owner, repo_name = repo.split("/", 1)
    github = get_github_client()
    use_case = AnalyzeRepositoryUseCase(github=github)
    try:
        report = _run_async(use_case.execute(owner, repo_name))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e

    if output and markdown:
        md = report_to_markdown(report)
        with open(output, "w") as f:
            f.write(md)
        console.print(f"[green]Markdown report written to {output}[/green]")
        return

    if markdown:
        console.print(Panel(report_to_markdown(report), title="Repository Health Report", border_style="blue"))
        return

    # Default: rich table summary
    table = Table(title="Repository Health Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Repository", report.repository)
    table.add_row("Documentation", f"{report.documentation.score}/10")
    table.add_row("Tests", report.tests.message)
    table.add_row("CI/CD", report.cicd.message)
    table.add_row("Dependencies", report.dependencies.message)
    table.add_row("Health Score", f"{report.health_score:.0f}%")
    console.print(table)


if __name__ == "__main__":
    app()
