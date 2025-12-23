import os
from typing import Optional, Tuple
from openai import OpenAI
from google import genai
from google.genai import types


API_CONFIGS = {
    "groq": {
        "prefix": "gsk_",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "has_native_search": False
    },
    "xai": {
        "prefix": "xai-",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-2-latest",
        "has_native_search": False
    },
    "gemini": {
        "prefix": "AIza",
        "base_url": None,
        "default_model": "gemini-2.0-flash",
        "has_native_search": True
    },
    "openai": {
        "prefix": "sk-",
        "base_url": None,
        "default_model": "gpt-4o",
        "has_native_search": True
    }
}


def detect_api_type(api_key: str) -> Tuple[str, str, bool]:
    if not api_key or len(api_key) < 10:
        return None, None, False
    
    for api_type, config in API_CONFIGS.items():
        if api_key.startswith(config["prefix"]):
            return api_type, config["default_model"], config["has_native_search"]
    
    return "groq", "llama-3.3-70b-versatile", False


class UnifiedLLM:
    
    def __init__(self, api_key: str, agent_name: str = "Agent", console=None):
        self.api_key = api_key
        self.agent_name = agent_name
        self.console = console
        self.api_type, self.model, self.has_native_search = detect_api_type(api_key)
        self._client = None
        self._gemini_client = None
        self._google_search_tool = None
        
        if self.api_type:
            self._setup_client()
    
    def _setup_client(self):
        if self.api_type == "gemini":
            self._gemini_client = genai.Client(api_key=self.api_key)
            self._google_search_tool = types.Tool(google_search=types.GoogleSearch())
        else:
            config = API_CONFIGS.get(self.api_type, {})
            base_url = config.get("base_url")
            
            if base_url:
                self._client = OpenAI(api_key=self.api_key, base_url=base_url)
            else:
                self._client = OpenAI(api_key=self.api_key)
    
    def is_valid(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 20 and self.api_type)
    
    def get_info(self) -> str:
        api_names = {"groq": "Groq", "openai": "OpenAI", "xai": "xAI", "gemini": "Gemini"}
        search_status = "Native Search" if self.has_native_search else "No Search"
        return f"{api_names.get(self.api_type, 'Unknown')} ({self.model}) [{search_status}]"
    
    def generate_with_search(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                return self._generate_gemini_with_search(prompt, system_prompt)
            elif self.api_type == "openai":
                return self._generate_openai_with_search(prompt, system_prompt)
            else:
                return self.generate(prompt, system_prompt)
        
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]API Error: {str(e)[:80]}[/dim red]")
            return None
    
    def _generate_openai_with_search(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        if self.console:
            self.console.print(f"      [cyan]Searching web...[/cyan]")
        
        full_input = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = self._client.responses.create(
            model=self.model,
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            input=full_input
        )
        
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'annotations') and content.annotations:
                            for annotation in content.annotations[:3]:
                                if hasattr(annotation, 'url') and self.console:
                                    title = getattr(annotation, 'title', 'Source')
                                    self.console.print(f"      [green]Source:[/green] [dim]{title[:50]}[/dim]")
        
        return response.output_text.strip() if hasattr(response, 'output_text') else None
    
    def _generate_gemini_with_search(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        if self.console:
            self.console.print(f"      [cyan]Searching web...[/cyan]")
        
        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
        
        config = types.GenerateContentConfig(tools=[self._google_search_tool])
        
        response = self._gemini_client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=config
        )
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                    for chunk in gm.grounding_chunks[:3]:
                        if hasattr(chunk, 'web') and chunk.web:
                            title = getattr(chunk.web, 'title', 'Source')
                            if self.console:
                                self.console.print(f"      [green]Source:[/green] [dim]{title}[/dim]")
        
        return response.text.strip()
    
    def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
                response = self._gemini_client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
                return response.text.strip()
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content.strip()
        
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]API Error: {str(e)[:80]}[/dim red]")
            return None
    
    def generate_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        return self.generate_with_search(prompt + "\n\nRespond with valid JSON only.", system_prompt)
