"""
AI Prediction Battle - Main Entry Point
V0: Predictions | V1: Text Debate | V2: Voice Debate
Supports interactive input - just run 'python main.py' to start!
"""

import warnings
import os

# Suppress pygame and other library warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import argparse
import sys
from dotenv import load_dotenv
from src.utils.console import console, print_header, print_section


def interactive_mode():
    """Run in interactive mode - prompts user for input."""
    print_header("🎯 AI PREDICTION BATTLE", "Intelligence Benchmark for Tech Predictions")
    
    console.print("\n[bold cyan]Enter a Polymarket event:[/bold cyan]")
    console.print("[dim]You can use: Event ID, URL, or Slug[/dim]")
    console.print("[dim]Example: 74949 or https://polymarket.com/event/... or event-slug[/dim]\n")
    
    event_input = console.input("[bold green]Event: [/bold green]").strip()
    
    if not event_input:
        console.print("[red]❌ No input provided.[/red]")
        return
    
    console.print("\n[bold cyan]Choose mode:[/bold cyan]")
    console.print("  1. Text debate (default)")
    console.print("  2. Voice debate (agents speak)")
    
    mode_input = console.input("\n[bold green]Mode (1/2): [/bold green]").strip() or "1"
    use_voice = mode_input == "2"
    
    # Run the battle
    from src.services.prediction_service import PredictionService
    
    print_section("PHASE 1: Independent Research & Predictions")
    console.print("[dim]Each agent researches independently with NO cross-leakage.[/dim]\n")
    
    service = PredictionService()
    predictions, agent_predictions = service.run_battle(event_input)
    
    if not predictions:
        console.print("[red]❌ No predictions generated. Check your API keys.[/red]")
        return
    
    resolved_event_id = predictions[0].event_id if predictions else event_input
    
    # Debate phase - pass fresh predictions, not from DB
    if use_voice:
        print_section("PHASE 2: Voice Debate")
        from src.services.voice_debate_service import VoiceDebateService
        voice_service = VoiceDebateService(service.all_agents)
        voice_service.run_voice_debate(resolved_event_id, agent_predictions)
    else:
        print_section("PHASE 2: Text Debate")
        console.print("[dim]Agents defend locked positions. NO changes allowed.[/dim]\n")
        from src.services.debate_service import DebateService
        debate_service = DebateService(service.all_agents)
        debate_service.run_debate(resolved_event_id, agent_predictions, rounds=2)


def main():
    load_dotenv()
    
    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    parser = argparse.ArgumentParser(
        description="AI Prediction Battle - Intelligence Benchmark for Tech Predictions"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Full battle: predict + debate
    run_parser = subparsers.add_parser("run", help="Run full battle: predictions + debate")
    run_parser.add_argument("event_id", type=str, help="Polymarket Event ID, URL, or Slug")
    run_parser.add_argument("--rounds", type=int, default=2, help="Number of debate rounds")
    run_parser.add_argument("--voice", action="store_true", help="Enable voice output (V2)")

    # Predict only
    predict_parser = subparsers.add_parser("predict", help="Run predictions only")
    predict_parser.add_argument("event_id", type=str, help="Polymarket Event ID")

    # Debate only
    debate_parser = subparsers.add_parser("debate", help="Run text debate only")
    debate_parser.add_argument("event_id", type=str, help="Event ID to debate")
    debate_parser.add_argument("--rounds", type=int, default=2, help="Debate rounds")

    # Voice debate
    voice_parser = subparsers.add_parser("voice", help="Run voice debate (V2)")
    voice_parser.add_argument("event_id", type=str, help="Event ID for voice debate")

    # Discover events
    subparsers.add_parser("discover", help="Discover trending tech events")
    
    # Test voice
    subparsers.add_parser("test-voice", help="Test voice generation")

    args = parser.parse_args()

    if args.command == "run":
        from src.services.prediction_service import PredictionService
        from src.services.debate_service import DebateService
        
        print_header("🎯 AI PREDICTION BATTLE", "Intelligence Benchmark for Tech Predictions")
        print_section("PHASE 1: Independent Research & Predictions")
        console.print("[dim]Each agent researches independently with NO cross-leakage.[/dim]\n")
        
        service = PredictionService()
        predictions, agent_predictions = service.run_battle(args.event_id)
        
        if not predictions:
            console.print("[red]❌ No predictions generated. Check your API keys.[/red]")
            return
        
        resolved_event_id = predictions[0].event_id if predictions else args.event_id
        
        if args.voice:
            print_section("PHASE 2: Voice Debate")
            from src.services.voice_debate_service import VoiceDebateService
            voice_service = VoiceDebateService(service.all_agents)
            voice_service.run_voice_debate(resolved_event_id, agent_predictions)
        else:
            print_section("PHASE 2: Text Debate")
            console.print("[dim]Agents defend locked positions. NO changes allowed.[/dim]\n")
            debate_service = DebateService(service.all_agents)
            debate_service.run_debate(resolved_event_id, agent_predictions, rounds=args.rounds)
        
    elif args.command == "predict":
        from src.services.prediction_service import PredictionService
        
        print_header("🎯 AI PREDICTION ENGINE", "V0 - Prediction Only")
        
        service = PredictionService()
        predictions, _ = service.run_battle(args.event_id)
        
        if predictions:
            console.print("\n[green]✅ Predictions locked and saved.[/green]")
                
    elif args.command == "debate":
        from src.services.prediction_service import PredictionService
        from src.services.debate_service import DebateService
        
        print_header("⚔️ AI DEBATE ENGINE", "V1 - Panel Discussion")
        console.print("[dim]Running predictions first...[/dim]\n")
        
        service = PredictionService()
        predictions, agent_predictions = service.run_battle(args.event_id)
        
        if agent_predictions:
            debate_service = DebateService(service.all_agents)
            debate_service.run_debate(predictions[0].event_id if predictions else args.event_id, agent_predictions, rounds=args.rounds)
        else:
            console.print("[red]❌ No predictions to debate.[/red]")
    
    elif args.command == "voice":
        from src.services.prediction_service import PredictionService
        from src.services.voice_debate_service import VoiceDebateService
        
        print_header("🎙️ VOICE DEBATE", "V2 - AI Agents Speak")
        console.print("[dim]Running predictions first...[/dim]\n")
        
        service = PredictionService()
        predictions, agent_predictions = service.run_battle(args.event_id)
        
        if agent_predictions:
            voice_service = VoiceDebateService(service.all_agents)
            voice_service.run_voice_debate(predictions[0].event_id if predictions else args.event_id, agent_predictions)
        else:
            console.print("[red]❌ No predictions to debate.[/red]")
        
    elif args.command == "discover":
        from src.services.polymarket_service import PolymarketService
        from rich.table import Table
        
        print_header("🔍 DISCOVER EVENTS", "Trending AI/Tech Events on Polymarket")
        
        events = PolymarketService.search_tech_events(limit=10)
        
        if events:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Event ID", style="dim")
            table.add_column("Title", max_width=50)
            table.add_column("Resolution Date")
            
            for e in events:
                table.add_row(e.event_id, e.title[:50], e.resolution_date[:10] if e.resolution_date else "N/A")
            
            console.print(table)
        else:
            console.print("[yellow]No events found.[/yellow]")
    
    elif args.command == "test-voice":
        from src.utils.voice import test_voice
        
        print_header("🎙️ VOICE TEST", "Testing Agent Voices")
        test_voice()
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
