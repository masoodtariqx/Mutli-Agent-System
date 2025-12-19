import os
from typing import List, Dict
from abc import ABC, abstractmethod
from tavily import TavilyClient
from src.models import PredictionOutput, EventMetadata, KeyFact

class BaseAgent(ABC):
    def __init__(self, name: str, model_name: str, archetype: str):
        self.name = name
        self.model_name = model_name
        self.archetype = archetype
        tavily_key = os.getenv("TAVILY_API_KEY")
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

    def research(self, query: str) -> str:
        """
        Performs web research using Tavily.
        """
        if not self.tavily:
            return "Research skipped: TAVILY_API_KEY not provided."
        try:
            response = self.tavily.search(query=query, search_depth="advanced")
            context = ""
            for result in response.get("results", []):
                context += f"Source: {result['url']}\nContent: {result['content']}\n\n"
            return context
        except Exception as e:
            return f"Research failed: {e}"

    @abstractmethod
    def has_valid_config(self) -> bool:
        pass

    @abstractmethod
    def generate_prediction(self, event: EventMetadata) -> PredictionOutput:
        pass
