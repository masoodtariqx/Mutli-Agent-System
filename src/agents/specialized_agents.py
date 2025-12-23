import os
import json
from src.agents.base_agent import BaseAgent
from src.models import PredictionOutput, EventMetadata
from src.prompts import SYSTEM_PROMPT_PREFIX, CHATGPT_ARCHETYPE, GROK_ARCHETYPE, GEMINI_ARCHETYPE, PREDICTION_PROMPT
from src.utils.api_adapter import UnifiedLLM
from src.utils.console import console


def clean_json(content: str) -> str:
    if not content:
        return "{}"
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content


class ChatGPTAgent(BaseAgent):

    def __init__(self):
        self._api_key = (
            os.getenv("CHATGPT_KEY") or
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("CHATGPT_API_KEY")
        )
        
        self._llm = UnifiedLLM(self._api_key, "ChatGPT", console) if self._api_key else None
        
        model_name = self._llm.model if self._llm and self._llm.is_valid() else "unknown"
        super().__init__("ChatGPT", model_name, "Precision-Oriented")
        
        if self.has_valid_config():
            console.print(f"   ✓ ChatGPT: {self._llm.get_info()}")

    def has_valid_config(self) -> bool:
        return self._llm is not None and self._llm.is_valid()

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        console.print(f"   [dim]Analyzing event...[/dim]")
        
        system = f"""{SYSTEM_PROMPT_PREFIX}
{CHATGPT_ARCHETYPE}

Analyze this prediction market event using your knowledge. Be precise and data-driven."""
        
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context="",
            event_id=event.event_id
        )
        
        response = self._llm.generate_json(user, system)
        if not response:
            raise Exception("API returned no response")
        
        data = json.loads(clean_json(response))
        return PredictionOutput(**data)


class GrokAgent(BaseAgent):

    def __init__(self):
        self._api_key = (
            os.getenv("GROK_KEY") or
            os.getenv("XAI_API_KEY") or 
            os.getenv("GROK_API_KEY")
        )
        
        self._llm = UnifiedLLM(self._api_key, "Grok", console) if self._api_key else None
        
        model_name = self._llm.model if self._llm and self._llm.is_valid() else "unknown"
        super().__init__("Grok", model_name, "Early-Signal Oriented")
        
        if self.has_valid_config():
            console.print(f"   ✓ Grok: {self._llm.get_info()}")

    def has_valid_config(self) -> bool:
        return self._llm is not None and self._llm.is_valid()

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        console.print(f"   [dim]Analyzing event...[/dim]")
        
        system = f"""{SYSTEM_PROMPT_PREFIX}
{GROK_ARCHETYPE}

Analyze this prediction market event. Look for early signals and unconventional insights."""
        
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context="",
            event_id=event.event_id
        )
        
        response = self._llm.generate_json(user, system)
        if not response:
            raise Exception("API returned no response")
        
        data = json.loads(clean_json(response))
        return PredictionOutput(**data)


class GeminiAgent(BaseAgent):

    def __init__(self):
        self._api_key = (
            os.getenv("GEMINI_KEY") or
            os.getenv("GEMINI_API_KEY")
        )
        
        self._llm = UnifiedLLM(self._api_key, "Gemini", console) if self._api_key else None
        
        model_name = self._llm.model if self._llm and self._llm.is_valid() else "unknown"
        super().__init__("Gemini", model_name, "Constraint-Oriented")
        
        if self.has_valid_config():
            console.print(f"   ✓ Gemini: {self._llm.get_info()}")

    def has_valid_config(self) -> bool:
        return self._llm is not None and self._llm.is_valid()

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        console.print(f"   [dim]Analyzing event...[/dim]")
        
        system = f"""{SYSTEM_PROMPT_PREFIX}
{GEMINI_ARCHETYPE}

Analyze this prediction market event. Focus on constraints, feasibility, and historical patterns."""
        
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context="",
            event_id=event.event_id
        )
        
        response = self._llm.generate_json(user, system)
        if not response:
            raise Exception("API returned no response")
        
        data = json.loads(clean_json(response))
        return PredictionOutput(**data)
