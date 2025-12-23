import os
import time
import random
from typing import List, Dict
from src.database import Database
from src.utils.console import (
    console, print_header, print_section, print_predictions_table,
    print_error, print_moderator
)
from src.utils.api_adapter import UnifiedLLM
from rich.panel import Panel

AGENT_PERSONAS = {
    "ChatGPT": """You are ChatGPT. Analytical, calm but firm.
STYLE: "I have to push back..." / "That's valid, but..." / "You're missing..."
Keep it natural. 2-3 sentences max.""",
    
    "Grok": """You are Grok. Casual, confident, provocative.
STYLE: "Nah, that's not it..." / "Look, I get it but..." / "Come on..."
Keep it punchy. 2-3 sentences max.""",
    
    "Gemini": """You are Gemini. Skeptical, detail-oriented realist.
STYLE: "In practice that falls apart..." / "You're ignoring the logistics..." / "Fair, but..."
Keep it grounded. 2-3 sentences max."""
}


class DebateService:
    
    def __init__(self, agents):
        self.db = Database()
        self.agents = [a for a in agents if a.has_valid_config()]
        self._llm = None
        self._setup_llm()
    
    def _setup_llm(self):
        for key_name in ["GEMINI_API_KEY", "GEMINI_KEY", "CHATGPT_KEY", "GROK_KEY", "OPENAI_API_KEY"]:
            key = os.getenv(key_name)
            if key and len(key) > 20:
                self._llm = UnifiedLLM(key, "Debate", console)
                if self._llm.is_valid():
                    return
        self._llm = None
    
    def _generate(self, prompt: str, agent_name: str) -> str:
        if not self._llm:
            return None
        
        persona = AGENT_PERSONAS.get(agent_name, "")
        system = f"""{persona}

You are in a LIVE debate with ChatGPT, Grok, and Gemini.
You are NOT forced to speak. YOU DECIDE.

YOUR OPTIONS:
- SPEAK: Say something (2-3 sentences)
- "PASS": Don't speak right now
- "I've made my point": When you're done

Be natural like a human expert."""
        
        for attempt in range(3):
            try:
                result = self._llm.generate(prompt, system)
                if result and len(result) > 2:
                    return result
            except Exception as e:
                if "429" in str(e):
                    time.sleep(5)
                time.sleep(2)
        return None

    def _show_thinking(self, agent_name: str):
        console.print(f"\n   [dim]{agent_name} considering...[/dim]", end="")
        time.sleep(0.3)
        console.print("\r" + " " * 40 + "\r", end="")

    def _print_speech(self, name: str, text: str, prediction: str):
        color = "green" if prediction == "YES" else "red"
        console.print(f"\n   [bold {color}]{name}[/bold {color}] [dim]({prediction})[/dim]")
        console.print(f"      [white]{text}[/white]")
        time.sleep(0.3)

    def run_debate(self, event_id: str, predictions: List[Dict], rounds: int = 3) -> Dict:
        if len(predictions) < 2:
            print_error("Need at least 2 predictions.")
            return {}
        
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            event_title = row[0] if row else "Unknown"
        
        print_header("LIVE DEBATE", event_title)
        
        console.print(Panel(
            "\n".join([
                f"[{'green' if p['prediction']=='YES' else 'red'}]{p['agent_name']}: {p['prediction']} ({p['probability']*100:.0f}%)[/]"
                for p in predictions
            ]),
            title="LOCKED PREDICTIONS",
            border_style="cyan"
        ))
        
        print_moderator("Floor is open. Anyone can start.", is_intro=True)
        
        transcript = []
        conversation = []
        agents_done = set()
        
        shuffled = predictions.copy()
        random.shuffle(shuffled)
        
        for p in shuffled:
            self._show_thinking(p['agent_name'])
            prompt = f"Event: {event_title}\nYour prediction: {p['prediction']}\nDo you want to start? Or PASS."
            response = self._generate(prompt, p['agent_name'])
            if response and response.strip().upper() != "PASS":
                self._print_speech(p['agent_name'], response, p['prediction'])
                transcript.append({"speaker": p['agent_name'], "text": response})
                conversation.append(f"{p['agent_name']}: {response}")
                if "made my point" in response.lower():
                    agents_done.add(p['agent_name'])
                break
        
        while len(agents_done) < len(predictions):
            available = [p for p in predictions if p['agent_name'] not in agents_done]
            if not available:
                break
            
            random.shuffle(available)
            
            for current in available:
                self._show_thinking(current['agent_name'])
                recent = "\n".join(conversation[-6:]) if conversation else "Nothing yet."
                
                prompt = f"""Event: {event_title}
Your prediction: {current['prediction']}

CONVERSATION:
{recent}

Do you want to respond, PASS, or say "I've made my point"?"""

                response = self._generate(prompt, current['agent_name'])
                
                if response:
                    clean = response.strip()
                    if clean.upper() == "PASS":
                        console.print(f"   [dim]{current['agent_name']} passes.[/dim]")
                    elif "made my point" in clean.lower():
                        self._print_speech(current['agent_name'], clean, current['prediction'])
                        conversation.append(f"{current['agent_name']}: {clean}")
                        agents_done.add(current['agent_name'])
                    else:
                        self._print_speech(current['agent_name'], clean, current['prediction'])
                        conversation.append(f"{current['agent_name']}: {clean}")
        
        print_moderator("All agents concluded.", is_intro=False)
        print_predictions_table(predictions)
        
        return {"event_id": event_id, "predictions": predictions, "transcript": transcript}
