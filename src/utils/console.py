"""
Beautiful Console Output - Full content display without truncation.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, DOUBLE
from typing import List, Dict

console = Console()


def print_header(title: str, subtitle: str = ""):
    """Print a beautiful header."""
    console.print()
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, box=DOUBLE, style="cyan", padding=(1, 2)))


def print_event(title: str, event_id: str, description: str = "", rules: str = "", date: str = ""):
    """Print event information captured from Polymarket."""
    content = f"[bold white]{title}[/bold white]\n"
    content += f"[dim]Event ID: {event_id}[/dim]"
    
    if description:
        content += f"\n\n[cyan]Description:[/cyan]\n{description[:300]}..." if len(description) > 300 else f"\n\n[cyan]Description:[/cyan]\n{description}"
    
    if rules:
        content += f"\n\n[cyan]Resolution Rules:[/cyan]\n{rules[:200]}..." if len(rules) > 200 else f"\n\n[cyan]Resolution Rules:[/cyan]\n{rules}"
    
    if date:
        content += f"\n\n[cyan]Resolution Date:[/cyan] {date}"
    
    console.print(Panel(
        content,
        title="📊 [bold]EVENT DATA FROM POLYMARKET[/bold]",
        border_style="blue"
    ))


def print_agents_status(active: List[str], inactive: List[str]):
    """Print active and inactive agents."""
    if inactive:
        console.print(f"[yellow]⚠️  Missing API keys:[/yellow] [dim]{', '.join(inactive)}[/dim]")
    if active:
        console.print(f"[green]🤖 Active Agents:[/green] [bold]{', '.join(active)}[/bold]")
    console.print()


def print_prediction(agent_name: str, prediction: str, probability: float, rationale: str, facts: List[Dict]):
    """Print a single prediction - FULL content, no truncation."""
    color = "green" if prediction == "YES" else "red" if prediction == "NO" else "yellow"
    
    content = Text()
    content.append(f"Prediction: ", style="dim")
    content.append(f"{prediction}\n", style=f"bold {color}")
    content.append(f"Probability: ", style="dim")
    content.append(f"{probability*100:.0f}%\n\n", style=f"bold {color}")
    
    # Full rationale - no truncation
    content.append(f"Rationale:\n", style="bold")
    content.append(f"{rationale}\n\n", style="white")
    
    # All claims - full content
    content.append(f"Key Claims:\n", style="bold")
    for i, fact in enumerate(facts, 1):
        claim = fact.get('claim', '')
        source = fact.get('source', 'No source')
        content.append(f"  {i}. {claim}\n", style="white")
        content.append(f"     Source: {source}\n", style="dim cyan")
    
    console.print(Panel(
        content,
        title=f"🔒 [bold]{agent_name}[/bold] PREDICTION",
        subtitle="[dim]Locked - Cannot be changed[/dim]",
        border_style=color,
        box=ROUNDED
    ))


def print_predictions_table(predictions: List[Dict]):
    """Print predictions summary table."""
    table = Table(title="🔒 Locked Predictions", box=ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="bold")
    table.add_column("Prediction", justify="center")
    table.add_column("Probability", justify="center")
    
    for p in predictions:
        pred = p.get('prediction', 'N/A')
        color = "green" if pred == "YES" else "red" if pred == "NO" else "yellow"
        prob = p.get('probability', 0)
        
        table.add_row(
            p.get('agent_name', 'Unknown'),
            f"[{color}]{pred}[/{color}]",
            f"[{color}]{prob*100:.0f}%[/{color}]"
        )
    
    console.print(table)
    console.print()


def print_moderator(text: str, is_intro: bool = True):
    """Print moderator message - full text."""
    title = "🎙️ MODERATOR" + (" - Opening" if is_intro else " - Summary")
    console.print(Panel(
        f"[italic]{text}[/italic]",
        title=title,
        border_style="magenta",
        box=ROUNDED
    ))
    console.print()


def print_section(title: str):
    """Print section divider."""
    console.print()
    console.rule(f"[bold]{title}[/bold]", style="dim")
    console.print()


def print_error(message: str):
    """Print error message."""
    console.print(f"[red]❌ {message}[/red]")


def print_success(message: str):
    """Print success message."""
    console.print(f"[green]✅ {message}[/green]")
