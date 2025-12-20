"""
V1 Text Debate Engine - Uses fresh predictions from current session
"""

import os
import time
from typing import List, Dict
import google.generativeai as genai
from src.database import Database
from src.utils.console import (
    console, print_header, print_section, print_predictions_table,
    print_error, print_moderator
)


class DebateService:
    """Text debate using fresh predictions from current session."""
    
    def __init__(self, agents):
        self.db = Database()
        self.agents = [a for a in agents if a.has_valid_config()]
        self._model = None
        self._configure_llm()
    
    def _configure_llm(self):
        for key_name in ["GEMINI_API_KEY", "CHATGPT_GEMINI_KEY", "GROK_GEMINI_KEY"]:
            key = os.getenv(key_name)
            if key and len(key) > 20:
                try:
                    genai.configure(api_key=key)
                    self._model = genai.GenerativeModel("gemini-2.0-flash")
                    return
                except:
                    continue
    
    def _generate_response(self, prompt: str) -> str:
        """Generate LLM response with retry."""
        if not self._model:
            return None
        
        max_attempts = 3
        wait_time = 10
        
        for attempt in range(max_attempts):
            try:
                response = self._model.generate_content(prompt)
                result = response.text.strip()
                if result and len(result) > 20:
                    return result
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_attempts - 1:
                        console.print(f"   [dim]⏳ Waiting for API ({wait_time}s)...[/dim]")
                        time.sleep(wait_time)
                        wait_time += 5
                    continue
                else:
                    time.sleep(2)
                    continue
        return None

    def run_debate(self, event_id: str, predictions: List[Dict], rounds: int = 2) -> Dict:
        """Run debate using fresh predictions from current session."""
        
        if len(predictions) < 2:
            print_error("Need at least 2 predictions for debate.")
            return {}
        
        # Get event title
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            event_title = row[0] if row else "Unknown Event"
        
        print_header("⚔️ PANEL DEBATE", event_title)
        
        # Show predictions
        console.print("\n[dim]Locked predictions:[/dim]")
        for pred in predictions:
            color = "green" if pred['prediction'] == "YES" else "red"
            console.print(f"   [{color}]{pred['agent_name']}: {pred['prediction']} ({pred['probability']*100:.0f}%)[/{color}]")
        console.print()
        
        print_moderator("All predictions are locked. Let's begin the panel discussion.", is_intro=True)
        
        transcript = []
        
        # Debate each agent's claims
        for target in predictions:
            target_name = target['agent_name']
            claims = target.get('key_facts', [])
            
            if not claims:
                continue
            
            print_section(f"Discussing {target_name}'s Position")
            
            for claim in claims:
                claim_text = claim.get('claim', '')
                source = claim.get('source', 'unknown')
                
                console.print(f"[yellow]📌 {target_name}'s Claim:[/yellow]")
                console.print(f"   \"{claim_text}\"")
                console.print(f"   [dim]Source: {source}[/dim]\n")
                
                other_agents = [p for p in predictions if p['agent_name'] != target_name]
                
                if len(other_agents) >= 1:
                    challenger1 = other_agents[0]['agent_name']
                    challenge = self._generate_response(
                        f"""You are {challenger1}. Challenge {target_name}'s claim:
"{claim_text}"

Start with "{target_name}," and explain why you disagree. 2 sentences."""
                    )
                    
                    if challenge:
                        console.print(f"   💬 [bold]{challenger1}:[/bold]")
                        console.print(f"      {challenge}\n")
                        transcript.append({"speaker": challenger1, "text": challenge})
                        
                        defense = self._generate_response(
                            f"""You are {target_name}. {challenger1} challenged you:
"{challenge}"

Respond to {challenger1}. Defend your position. Start with "{challenger1}," 2 sentences."""
                        )
                        
                        if defense:
                            console.print(f"   💬 [bold]{target_name}:[/bold]")
                            console.print(f"      {defense}\n")
                            transcript.append({"speaker": target_name, "text": defense})
                
                if len(other_agents) >= 2:
                    challenger2 = other_agents[1]['agent_name']
                    addition = self._generate_response(
                        f"""You are {challenger2}. {target_name} and {challenger1} are debating.
Add your perspective. 2 sentences."""
                    )
                    
                    if addition:
                        console.print(f"   💬 [bold]{challenger2}:[/bold]")
                        console.print(f"      {addition}\n")
                        transcript.append({"speaker": challenger2, "text": addition})
        
        print_moderator("This concludes our panel discussion. All predictions remain locked.", is_intro=False)
        print_predictions_table(predictions)
        
        return {"event_id": event_id, "predictions": predictions, "transcript": transcript}
