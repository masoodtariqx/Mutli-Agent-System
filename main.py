import argparse
from dotenv import load_dotenv
from src.services.prediction_service import PredictionService

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="AI Prediction Battle - Tech Events")
    subparsers = parser.add_subparsers(dest="command")

    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Run a prediction battle for a given event ID")
    predict_parser.add_argument("event_id", type=str, help="Polymarket Gamma Event ID")

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover active tech events on Polymarket")
    discover_parser.add_argument("--limit", type=int, default=10, help="Number of events to show")

    # Debate command
    debate_parser = subparsers.add_parser("debate", help="Start a debate between agents for a predicted event")
    debate_parser.add_argument("event_id", type=str, help="Event ID to debate")
    debate_parser.add_argument("--rounds", type=int, default=3, help="Number of debate rounds")

    args = parser.parse_args()

    if args.command == "predict":
        service = PredictionService()
        service.run_battle(args.event_id)
    elif args.command == "discover":
        from src.services.polymarket_service import PolymarketService
        print("\n🔍 Searching for active tech events on Polymarket...")
        events = PolymarketService.search_tech_events(limit=args.limit)
        if not events:
            print("No events found.")
        else:
            print(f"{'ID':<10} | {'Title':<45} | {'Ends'}")
            print("-" * 75)
            for e in events:
                date_str = e.resolution_date.split("T")[0] if "T" in e.resolution_date else e.resolution_date
                print(f"{e.event_id:<10} | {e.title[:45]:<45} | {date_str}")
            print("\n💡 Tip: Use 'python main.py predict <ID>' to start a battle for one of these events.")
    elif args.command == "debate":
        from src.services.prediction_service import PredictionService
        from src.services.debate_service import DebateService
        
        # We need the agents from the service to ensure config is shared
        pred_service = PredictionService()
        debate_service = DebateService(pred_service.all_agents)
        debate_service.run_debate(args.event_id, rounds=args.rounds)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
