import argparse
import os
from dotenv import load_dotenv
from src.services.prediction_service import PredictionService

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="AI Prediction Battle - V0 Prediction Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # V0 Predict command
    predict_parser = subparsers.add_parser("predict", help="Run a prediction battle for a specific Polymarket Event ID")
    predict_parser.add_argument("event_id", type=str, help="The Polymarket Gamma Event ID")

    args = parser.parse_args()

    if args.command == "predict":
        service = PredictionService()
        service.run_battle(args.event_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
