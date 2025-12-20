"""
Prediction Service - Orchestrates predictions with proper agent tracking
Returns both predictions list and agent_predictions dict for debate
"""

import os
from typing import List, Tuple, Dict
from src.agents.specialized_agents import ChatGPTAgent, GrokAgent, GeminiAgent
from src.services.polymarket_service import PolymarketService
from src.database import Database
from src.models import PredictionOutput
from src.utils.console import (
    console, print_header, print_event, print_agents_status,
    print_prediction, print_predictions_table, print_error, print_section
)


class PredictionService:
    """Orchestrates prediction battles with proper agent tracking."""
    
    def __init__(self):
        self.db = Database()
        self.all_agents = [
            ChatGPTAgent(),
            GrokAgent(),
            GeminiAgent(),
        ]

    def _get_active_agents(self):
        active = []
        inactive = []
        for agent in self.all_agents:
            if agent.has_valid_config():
                active.append(agent)
            else:
                inactive.append(agent.name)
        return active, inactive

    def _format_error(self, error: str) -> str:
        """Clean up error messages."""
        if "429" in str(error) or "quota" in str(error).lower():
            return "Rate limit exceeded. Wait 1 minute."
        if "401" in str(error) or "unauthorized" in str(error).lower() or "invalid" in str(error).lower():
            return "Invalid API key."
        if "404" in str(error) or "not found" in str(error).lower():
            return "Model not found."
        return str(error).split('\n')[0][:80]

    def run_battle(self, event_id: str):
        """Returns (predictions_list, agent_predictions_dict) for debate."""
        
        # 1. Fetch Event
        event = PolymarketService.get_event_details(event_id)
        if not event:
            print_error(f"Failed to fetch event: {event_id}")
            return [], {}

        # Show full event data captured from Polymarket
        print_event(
            event.title, 
            event.event_id, 
            event.description, 
            event.resolution_rules, 
            event.resolution_date
        )
        self.db.save_event(event)

        # 2. Check Active Agents
        active_agents, inactive_names = self._get_active_agents()
        print_agents_status([a.name for a in active_agents], inactive_names)
        
        if not active_agents:
            print_error("No agents configured! Add API keys to .env")
            return [], {}

        # 3. Run Predictions - Track with agent names
        predictions: List[PredictionOutput] = []
        agent_predictions: List[Dict] = []  # For debate
        
        for agent in active_agents:
            print_section(f"{agent.name} Researching")
            
            try:
                pred = agent.generate_prediction(event)
                self.db.save_prediction(agent.name, pred)
                predictions.append(pred)
                
                # Store for debate - with agent name
                agent_predictions.append({
                    "agent_name": agent.name,
                    "prediction": pred.prediction.value,
                    "probability": pred.probability,
                    "rationale": pred.rationale,
                    "key_facts": [{"claim": f.claim, "source": f.source} for f in pred.key_facts]
                })
                
                # Beautiful prediction output
                print_prediction(
                    agent.name,
                    pred.prediction.value,
                    pred.probability,
                    pred.rationale,
                    [{"claim": f.claim, "source": f.source} for f in pred.key_facts]
                )
                    
            except Exception as e:
                print_error(f"{agent.name} failed: {self._format_error(str(e))}")

        # Summary table
        if agent_predictions:
            print_section("Predictions Summary")
            print_predictions_table(agent_predictions)
        
        return predictions, agent_predictions
