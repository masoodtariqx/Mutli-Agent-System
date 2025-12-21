"""
Specialized Agents with Tool Calling Support
LLM decides when to search - shows research activity in real-time
"""

import os
import json
from src.agents.base_agent import BaseAgent
from src.models import PredictionOutput, EventMetadata
from src.prompts import SYSTEM_PROMPT_PREFIX, CHATGPT_ARCHETYPE, GROK_ARCHETYPE, GEMINI_ARCHETYPE, PREDICTION_PROMPT
from src.utils.api_adapter import UnifiedLLM
from src.utils.console import console


def clean_json(content: str) -> str:
    """Strip markdown/code fences from JSON."""
    if not content:
        return "{}"
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content


class ChatGPTAgent(BaseAgent):
    """ChatGPT - Precision-focused with tool calling for live research."""

    def __init__(self):
        self._api_key = (
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("CHATGPT_API_KEY") or 
            os.getenv("CHATGPT_GROQ_KEY") or
            os.getenv("CHATGPT_GEMINI_KEY")
        )
        
        self._llm = UnifiedLLM(self._api_key, "ChatGPT", console) if self._api_key else None
        
        model_name = self._llm.model if self._llm and self._llm.is_valid() else "unknown"
        super().__init__("ChatGPT", model_name, "Precision-Oriented")
        
        if self.has_valid_config():
            console.print(f"   ✓ ChatGPT: {self._llm.get_info()}")

    def has_valid_config(self) -> bool:
        return self._llm is not None and self._llm.is_valid()

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        console.print(f"   [dim]📊 Analyzing event...[/dim]")
        
        system = f"""{SYSTEM_PROMPT_PREFIX}
{CHATGPT_ARCHETYPE}

You have access to a web_search tool. Use it to find current, factual information to support your analysis.
Search for relevant data before making your prediction."""
        
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context="Use web_search tool to research current facts.",
            event_id=event.event_id
        )
        
        response = self._llm.generate_json(user, system)
        if not response:
            raise Exception("API returned no response")
        
        data = json.loads(clean_json(response))
        return PredictionOutput(**data)


class GrokAgent(BaseAgent):
    """Grok - Early-Signal focused with tool calling for live research."""

    def __init__(self):
        self._api_key = (
            os.getenv("XAI_API_KEY") or 
            os.getenv("GROK_API_KEY") or 
            os.getenv("GROK_GROQ_KEY") or
            os.getenv("GROK_GEMINI_KEY")
        )
        
        self._llm = UnifiedLLM(self._api_key, "Grok", console) if self._api_key else None
        
        model_name = self._llm.model if self._llm and self._llm.is_valid() else "unknown"
        super().__init__("Grok", model_name, "Early-Signal Oriented")
        
        if self.has_valid_config():
            console.print(f"   ✓ Grok: {self._llm.get_info()}")

    def has_valid_config(self) -> bool:
        return self._llm is not None and self._llm.is_valid()

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        console.print(f"   [dim]📊 Analyzing event...[/dim]")
        
        system = f"""{SYSTEM_PROMPT_PREFIX}
{GROK_ARCHETYPE}

You have access to a web_search tool. Use it to find early signals, rumors, social sentiment, and trending discussions.
Search for unconventional sources before making your prediction."""
        
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context="Use web_search tool to find early signals and trends.",
            event_id=event.event_id
        )
        
        response = self._llm.generate_json(user, system)
        if not response:
            raise Exception("API returned no response")
        
        data = json.loads(clean_json(response))
        return PredictionOutput(**data)


class GeminiAgent(BaseAgent):
    """Gemini - Constraint-focused with tool calling for live research."""

    def __init__(self):
        self._api_key = (
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("GEMINI_GROQ_KEY")
        )
        
        self._llm = UnifiedLLM(self._api_key, "Gemini", console) if self._api_key else None
        
        model_name = self._llm.model if self._llm and self._llm.is_valid() else "unknown"
        super().__init__("Gemini", model_name, "Constraint-Oriented")
        
        if self.has_valid_config():
            console.print(f"   ✓ Gemini: {self._llm.get_info()}")

    def has_valid_config(self) -> bool:
        return self._llm is not None and self._llm.is_valid()

    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        console.print(f"   [dim]📊 Analyzing event...[/dim]")
        
        system = f"""{SYSTEM_PROMPT_PREFIX}
{GEMINI_ARCHETYPE}

You have access to a web_search tool. Use it to find historical data, constraints, and feasibility analysis.
Search for analytical sources before making your prediction."""
        
        user = PREDICTION_PROMPT.format(
            title=event.title,
            description=event.description,
            rules=event.resolution_rules,
            date=event.resolution_date,
            context="Use web_search tool to research constraints and feasibility.",
            event_id=event.event_id
        )
        
        response = self._llm.generate_json(user, system)
        if not response:
            raise Exception("API returned no response")
        
        data = json.loads(clean_json(response))
        return PredictionOutput(**data)
