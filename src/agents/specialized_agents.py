"""
Specialized Agents - ChatGPT, Grok, and Gemini
Supports NATIVE APIs: OpenAI, xAI, and Google Gemini.
Falls back to Gemini if using GEMINI_ prefixed keys.
"""

import os
import json
import google.generativeai as genai
from openai import OpenAI
from src.agents.base_agent import BaseAgent
from src.models import PredictionOutput, EventMetadata
from src.prompts import SYSTEM_PROMPT_PREFIX, CHATGPT_ARCHETYPE, GROK_ARCHETYPE, GEMINI_ARCHETYPE, PREDICTION_PROMPT


def clean_json(content: str) -> str:
    """Strip markdown/code fences from JSON."""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content


def detect_best_gemini_model(api_key: str) -> str:
    """Auto-detect best available Gemini model."""
    if not api_key or len(api_key) < 20:
        return "gemini-2.0-flash"
    
    try:
        genai.configure(api_key=api_key)
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                available.append(name)
        
        for preferred in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash"]:
            if preferred in available:
                return preferred
        
        return available[0] if available else "gemini-2.0-flash"
    except:
        return "gemini-2.0-flash"


class ChatGPTAgent(BaseAgent):
    """ChatGPT - Precision-focused. Uses OpenAI API (or Gemini fallback)."""

    def __init__(self):
        # Check for real OpenAI key first
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._gemini_key = os.getenv("CHATGPT_GEMINI_KEY")
        
        # Determine which API to use
        self._use_openai = bool(self._openai_key and self._openai_key.startswith("sk-"))
        
        if self._use_openai:
            self._client = OpenAI(api_key=self._openai_key)
            model_name = "gpt-4o"  # Best model
            print(f"   ✓ ChatGPT using: OpenAI API ({model_name})")
        else:
            self._client = None
            model_name = detect_best_gemini_model(self._gemini_key) if self._gemini_key else "gemini-2.0-flash"
            if self._gemini_key and len(self._gemini_key) > 20:
                print(f"   ✓ ChatGPT using: Gemini fallback ({model_name})")
        
        self._model = None
        super().__init__("ChatGPT", model_name, "Precision-Oriented")

    def has_valid_config(self) -> bool:
        if self._use_openai:
            return bool(self._openai_key) and len(self._openai_key) > 20
        return bool(self._gemini_key) and len(self._gemini_key) > 20 and not self._gemini_key.startswith("your_")

    @property
    def model(self):
        if not self._use_openai and not self._model:
            genai.configure(api_key=self._gemini_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        context = self.research(f"{event.title} official sources documentation")
        system = f"{SYSTEM_PROMPT_PREFIX}\n{CHATGPT_ARCHETYPE}"
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context=context,
            event_id=event.event_id
        )
        
        if self._use_openai:
            # Use OpenAI API
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user + "\n\nRespond with valid JSON only."}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
        else:
            # Use Gemini fallback
            prompt = f"{system}\n\n{user}\n\nRespond with valid JSON only."
            response = self.model.generate_content(prompt)
            data = json.loads(clean_json(response.text.strip()))
        
        return PredictionOutput(**data)


class GrokAgent(BaseAgent):
    """Grok - Early-Signal focused. Uses xAI API (or Gemini fallback)."""

    def __init__(self):
        # Check for real xAI key first
        self._xai_key = os.getenv("XAI_API_KEY")
        self._gemini_key = os.getenv("GROK_GEMINI_KEY")
        
        # xAI uses OpenAI-compatible API
        self._use_xai = bool(self._xai_key and self._xai_key.startswith("xai-"))
        
        if self._use_xai:
            self._client = OpenAI(api_key=self._xai_key, base_url="https://api.x.ai/v1")
            model_name = "grok-2-latest"  # Best Grok model
            print(f"   ✓ Grok using: xAI API ({model_name})")
        else:
            self._client = None
            model_name = detect_best_gemini_model(self._gemini_key) if self._gemini_key else "gemini-2.0-flash"
            if self._gemini_key and len(self._gemini_key) > 20:
                print(f"   ✓ Grok using: Gemini fallback ({model_name})")
        
        self._model = None
        super().__init__("Grok", model_name, "Early-Signal Oriented")

    def has_valid_config(self) -> bool:
        if self._use_xai:
            return bool(self._xai_key) and len(self._xai_key) > 20
        return bool(self._gemini_key) and len(self._gemini_key) > 20 and not self._gemini_key.startswith("your_")

    @property
    def model(self):
        if not self._use_xai and not self._model:
            genai.configure(api_key=self._gemini_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        context = self.research(f"{event.title} rumors leaks social sentiment trends")
        system = f"{SYSTEM_PROMPT_PREFIX}\n{GROK_ARCHETYPE}"
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context=context,
            event_id=event.event_id
        )
        
        if self._use_xai:
            # Use xAI API (OpenAI-compatible)
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user + "\n\nRespond with valid JSON only."}
                ]
            )
            data = json.loads(clean_json(response.choices[0].message.content))
        else:
            # Use Gemini fallback
            prompt = f"{system}\n\n{user}\n\nRespond with valid JSON only."
            response = self.model.generate_content(prompt)
            data = json.loads(clean_json(response.text.strip()))
        
        return PredictionOutput(**data)


class GeminiAgent(BaseAgent):
    """Gemini - Constraint-focused. Uses Google Gemini API."""

    def __init__(self):
        self._api_key = os.getenv("GEMINI_API_KEY")
        self._model = None
        model_name = detect_best_gemini_model(self._api_key) if self._api_key else "gemini-2.0-flash"
        super().__init__("Gemini", model_name, "Constraint-Oriented")
        if self.has_valid_config():
            print(f"   ✓ Gemini using: {model_name}")

    def has_valid_config(self) -> bool:
        key = self._api_key
        return bool(key) and len(key) > 20 and not key.startswith("your_")

    @property
    def model(self):
        if not self._model:
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        context = self.research(f"{event.title} historical constraints feasibility")
        system = f"{SYSTEM_PROMPT_PREFIX}\n{GEMINI_ARCHETYPE}"
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context=context,
            event_id=event.event_id
        )
        
        prompt = f"{system}\n\n{user}\n\nRespond with valid JSON only."
        response = self.model.generate_content(prompt)
        data = json.loads(clean_json(response.text.strip()))
        return PredictionOutput(**data)
