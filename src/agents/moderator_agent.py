import os
import json
from openai import OpenAI
from src.prompts import MODERATOR_SYSTEM_PROMPT

class ModeratorAgent:
    def __init__(self):
        self.model_name = "gpt-4o" # Using a high-level model for moderation
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def provide_direction(self, event_title: str, predictions_summary: str, transcript: str) -> str:
        """
        Analyzes the debate so far and provides direction for the next turn.
        """
        user_content = f"""
EVENT: {event_title}

INITIAL PREDICTIONS:
{predictions_summary}

DEBATE TRANSCRIPT SO FAR:
{transcript}

Analyze the factual disagreements and specify which agent should speak next and what claim they should address.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": MODERATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Moderation failed: {e}"
