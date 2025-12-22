"""
Natural Voice Debate Engine - Free-flowing conversation with TTS
Agents speak naturally like real experts - High Tension Mode
"""

import os
import time
from typing import List, Dict
from src.database import Database
from src.utils.voice import speak
from src.utils.console import (
    console, print_header, print_section, print_predictions_table, print_error
)
from src.utils.api_adapter import UnifiedLLM
from rich.panel import Panel


class VoiceDebateService:
    """Natural voice debate with free-flowing conversation."""
    
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

    def _speak_agent(self, agent_name: str, text: str, prediction: str):
        """Print and speak agent's words."""
        color = "green" if prediction == "YES" else "red" if prediction == "NO" else "yellow"
        console.print(f"\n   💬 [bold {color}]{agent_name}[/bold {color}] [dim]({prediction})[/dim]")
        console.print(f"      [white]{text}[/white]")
        speak(text, agent_name)

    def run_voice_debate(self, event_id: str, predictions: List[Dict], rounds: int = 2) -> Dict:
        """Run natural voice debate."""
        
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
        
        print_header("🎙️ LIVE EXPERT PANEL (HIGH TENSION)", event_title)
        
        # Build context
        predictions_context = "\n".join([
            f"- {p['agent_name']} predicts {p['prediction']} ({p['probability']*100:.0f}%)"
            for p in predictions
        ])
        
        # Check consensus
        all_yes = all(p['prediction'] == "YES" for p in predictions)
        all_no = all(p['prediction'] == "NO" for p in predictions)
        consensus_mode = all_yes or all_no

        # Show locked predictions
        console.print(Panel(
            "\n".join([
                f"[{'green' if p['prediction']=='YES' else 'red'}]● {p['agent_name']}: {p['prediction']} ({p['probability']*100:.0f}%)[/]"
                for p in predictions
            ]),
            title="🔒 [bold]LOCKED PREDICTIONS[/bold]",
            border_style="cyan"
        ))
        
        # Moderator opens
        intro = "Welcome to the panel. I want a sharp debate today. Don't be polite."
        if consensus_mode:
            intro += " Since you all agree, I want deeper analysis. Find the risks. Why might you be wrong?"
            
        console.print(f"\n[magenta]🎙️ Moderator:[/magenta] {intro}")
        speak(intro, "Moderator")
        
        transcript = []
        conversation_history = []
        
        # Natural conversation rounds
        for round_num in range(1, rounds + 1):
            print_section(f"Discussion Round {round_num}")
            
            for i, current_agent in enumerate(predictions):
                agent_name = current_agent['agent_name']
                agent_prediction = current_agent['prediction']
                
                history_text = "\n".join(conversation_history[-4:]) if conversation_history else "Start of discussion."
                
                # Dynamic Prompting
                base_instruction = f"You are {agent_name}."
                if agent_name == "ChatGPT":
                    base_instruction += " You are a Rigorous Skeptic. Be arrogant about data."
                elif agent_name == "Grok":
                    base_instruction += " You are an Edgy Provocateur. Challenge the narrative."
                elif agent_name == "Gemini":
                    base_instruction += " You are a Pragmatic Realist. Focus on constraints."

                if consensus_mode and round_num > 1:
                    instruction = "Everyone agrees. Play Devil's Advocate. Tell a short story about how we could be wrong."
                else:
                    instruction = "Respond naturally. Use an analogy or a 'human' example. Don't sound like a bot."

                if round_num == 1 and i == 0:
                    prompt = f"""{base_instruction}
Event: {event_title}
Open the discussion naturally. Explain your view as if talking to colleagues. Express a complete thought."""
                else:
                    prompt = f"""{base_instruction}
Event: {event_title}
Recent discussion:
{history_text}

{instruction}
Respond naturally. You can speak for 3-4 sentences to explain your point."""
                
                response = self._generate_response(prompt)
                
                if response:
                    self._speak_agent(agent_name, response, agent_prediction)
                    transcript.append({"speaker": agent_name, "text": response})
                    conversation_history.append(f"{agent_name}: {response}")
        
        # Closing
        closing = "Debate concluded. The market is the ultimate judge."
        console.print(f"\n[magenta]🎙️ Moderator:[/magenta] {closing}")
        speak(closing, "Moderator")
        
        print_predictions_table(predictions)
        
        return {"event_id": event_id, "predictions": predictions, "transcript": transcript}
