"""
Natural Debate Engine - Free-flowing conversation like real experts
No rigid structure - agents respond naturally to each other
"""

import os
import time
from typing import List, Dict
from src.database import Database
from src.utils.console import (
    console, print_header, print_section, print_predictions_table,
    print_error, print_moderator
)
from src.utils.api_adapter import UnifiedLLM
from rich.panel import Panel
from rich.text import Text


class DebateService:
    """Natural free-flowing debate between AI agents."""
    
    def __init__(self, agents):
        self.db = Database()
        self.agents = [a for a in agents if a.has_valid_config()]
        self._llm = None
        self._setup_llm()
    
    def _setup_llm(self):
        for key_name in ["GEMINI_API_KEY", "CHATGPT_GROQ_KEY", "GROK_GROQ_KEY", "OPENAI_API_KEY"]:
            key = os.getenv(key_name)
            if key and len(key) > 20:
                self._llm = UnifiedLLM(key, "Debate", console)
                if self._llm.is_valid():
                    return
        self._llm = None
    
    def _generate_response(self, prompt: str) -> str:
        if not self._llm:
            return None
        
        max_attempts = 3
        wait_time = 5
        
        for attempt in range(max_attempts):
            try:
                result = self._llm.generate(prompt)
                if result and len(result) > 20:
                    return result
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    if attempt < max_attempts - 1:
                        console.print(f"   [dim]⏳ Waiting ({wait_time}s)...[/dim]")
                        time.sleep(wait_time)
                        wait_time += 5
                    continue
                else:
                    time.sleep(2)
                    continue
        return None

    def _print_agent_speech(self, agent_name: str, text: str, prediction: str):
        """Print agent speech in a beautiful panel."""
        color = "green" if prediction == "YES" else "red" if prediction == "NO" else "yellow"
        console.print(f"\n   💬 [bold {color}]{agent_name}[/bold {color}] [dim]({prediction})[/dim]")
        console.print(f"      [white]{text}[/white]")

    def run_debate(self, event_id: str, predictions: List[Dict], rounds: int = 3) -> Dict:
        """Run natural free-flowing debate."""
        
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
        
        print_header("⚔️ EXPERT PANEL DEBATE", event_title)
        
        # Build context for natural conversation
        predictions_context = "\n".join([
            f"- {p['agent_name']} predicts {p['prediction']} ({p['probability']*100:.0f}%): {p['rationale'][:100]}..."
            for p in predictions
        ])
        
        # Show locked predictions summary
        console.print(Panel(
            "\n".join([
                f"[{'green' if p['prediction']=='YES' else 'red'}]● {p['agent_name']}: {p['prediction']} ({p['probability']*100:.0f}%)[/]"
                for p in predictions
            ]),
            title="🔒 [bold]LOCKED PREDICTIONS[/bold]",
            border_style="cyan"
        ))
        
        # Moderator opens
        print_moderator("Welcome to our expert panel. Each analyst has made their prediction. Let's have a natural discussion about your reasoning and where you disagree.", is_intro=True)
        
        transcript = []
        conversation_history = []
        
        # Natural conversation rounds
        for round_num in range(1, rounds + 1):
            print_section(f"Discussion Round {round_num}")
            
            for i, current_agent in enumerate(predictions):
                agent_name = current_agent['agent_name']
                agent_prediction = current_agent['prediction']
                other_agents = [p for p in predictions if p['agent_name'] != agent_name]
                
                # Build conversation context
                history_text = "\n".join(conversation_history[-6:]) if conversation_history else "This is the start of the discussion."
                
                if round_num == 1 and i == 0:
                    # First speaker opens
                    prompt = f"""You are {agent_name}, an AI analyst who predicted {agent_prediction}.

Event: {event_title}

Your prediction: {agent_prediction} ({current_agent['probability']*100:.0f}%)
Your reasoning: {current_agent['rationale']}

Other panelists' positions:
{predictions_context}

Open the discussion by explaining your key argument. Be conversational, confident, and direct. 2-3 sentences."""
                
                elif round_num == 1:
                    # Others respond to opening
                    prompt = f"""You are {agent_name}, an AI analyst who predicted {agent_prediction}.

Event: {event_title}

Your prediction: {agent_prediction} ({current_agent['probability']*100:.0f}%)

Recent discussion:
{history_text}

Respond to what was just said. You can agree, disagree, or add a new perspective. Be natural and conversational like a real expert. Address others by name. 2-3 sentences."""
                
                else:
                    # Free flowing discussion
                    prompt = f"""You are {agent_name}, an AI analyst who predicted {agent_prediction}.

Event: {event_title}

Your position: {agent_prediction}

Conversation so far:
{history_text}

Continue the natural discussion. You can:
- Challenge someone's point
- Defend your position
- Acknowledge a good argument
- Raise a new consideration

Be conversational like a real expert panelist. Address others by name when responding to them. 2-3 sentences."""
                
                response = self._generate_response(prompt)
                
                if response:
                    self._print_agent_speech(agent_name, response, agent_prediction)
                    transcript.append({"speaker": agent_name, "text": response})
                    conversation_history.append(f"{agent_name}: {response}")
        
        # Closing statements
        print_section("Closing Statements")
        
        for agent in predictions:
            agent_name = agent['agent_name']
            agent_prediction = agent['prediction']
            
            prompt = f"""You are {agent_name}. Give a brief closing statement (1-2 sentences) summarizing why you stand by your {agent_prediction} prediction after this discussion."""
            
            response = self._generate_response(prompt)
            if response:
                self._print_agent_speech(agent_name, response, agent_prediction)
                transcript.append({"speaker": agent_name, "text": response})
        
        print_moderator("Thank you to our expert panel. All predictions remain locked. The market will ultimately decide.", is_intro=False)
        
        # Final summary
        print_predictions_table(predictions)
        
        return {"event_id": event_id, "predictions": predictions, "transcript": transcript}
