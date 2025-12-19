import os
import json
from openai import OpenAI
import google.generativeai as genai
from src.agents.base_agent import BaseAgent
from src.models import PredictionOutput, EventMetadata, PredictionOutcome
from src.prompts import (
    SYSTEM_PROMPT_PREFIX, CHATGPT_ARCHETYPE, GROK_ARCHETYPE, GEMINI_ARCHETYPE, PREDICTION_PROMPT
)

class ChatGPTAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agent A", "gpt-4-turbo", "Precision-Oriented")
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client

    def has_valid_config(self) -> bool:
        key = os.getenv("OPENAI_API_KEY")
        return bool(key) and not key.startswith("your_")

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        context = self.research(f"{event.title} {event.description}")
        system_content = f"{SYSTEM_PROMPT_PREFIX}\n{CHATGPT_ARCHETYPE}"
        user_content = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context=context,
            event_id=event.event_id
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return PredictionOutput(**data)

    def debate_turn(self, moderator_direction: str, transcript: str, original_prediction: str, other_predictions: str) -> str:
        system_content = f"{SYSTEM_PROMPT_PREFIX}\n{CHATGPT_ARCHETYPE}"
        user_content = DEBATE_TURN_PROMPT.format(
            moderator_direction=moderator_direction,
            transcript=transcript,
            original_prediction=original_prediction,
            other_predictions=other_predictions
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content

class GrokAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agent B", "grok-beta", "Early-Signal Oriented")
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = OpenAI(
                api_key=os.getenv("XAI_API_KEY"),
                base_url="https://api.x.ai/v1"
            )
        return self._client

    def has_valid_config(self) -> bool:
        key = os.getenv("XAI_API_KEY")
        return bool(key) and not key.startswith("your_")

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        context = self.research(f"latest rumors leaks social sentiment {event.title}")
        system_content = f"{SYSTEM_PROMPT_PREFIX}\n{GROK_ARCHETYPE}"
        user_content = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context=context,
            event_id=event.event_id
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return PredictionOutput(**data)

    def debate_turn(self, moderator_direction: str, transcript: str, original_prediction: str, other_predictions: str) -> str:
        system_content = f"{SYSTEM_PROMPT_PREFIX}\n{GROK_ARCHETYPE}"
        user_content = DEBATE_TURN_PROMPT.format(
            moderator_direction=moderator_direction,
            transcript=transcript,
            original_prediction=original_prediction,
            other_predictions=other_predictions
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content

class GeminiAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agent C", "gemini-1.5-flash", "Constraint-Oriented")
        self._model = None

    @property
    def model(self):
        if not self._model:
            api_key = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def has_valid_config(self) -> bool:
        key = os.getenv("GEMINI_API_KEY")
        return bool(key) and not key.startswith("your_")

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        context = self.research(f"historical feasibility technical constraints {event.title}")
        system_content = f"{SYSTEM_PROMPT_PREFIX}\n{GEMINI_ARCHETYPE}"
        user_content = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context=context,
            event_id=event.event_id
        )

        # Gemini doesn't have a direct 'response_format' in the same way, but can be prompted
        # Using a restricted prompt for JSON
        prompt = f"{system_content}\n\n{user_content}\n\nStrictly output valid JSON."
        response = self.model.generate_content(prompt)
        
        # Simple JSON extract (might need robustness)
        content = response.text.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(content)
        return PredictionOutput(**data)

    def debate_turn(self, moderator_direction: str, transcript: str, original_prediction: str, other_predictions: str) -> str:
        system_content = f"{SYSTEM_PROMPT_PREFIX}\n{GEMINI_ARCHETYPE}"
        user_content = DEBATE_TURN_PROMPT.format(
            moderator_direction=moderator_direction,
            transcript=transcript,
            original_prediction=original_prediction,
            other_predictions=other_predictions
        )

        prompt = f"{system_content}\n\n{user_content}"
        response = self.model.generate_content(prompt)
        return response.text
