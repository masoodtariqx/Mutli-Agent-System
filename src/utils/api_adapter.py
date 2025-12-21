"""
Unified API Adapter with Tool Calling Support
Auto-detects provider, supports function calling for live web search
"""

import os
import json
from typing import Optional, Tuple, List, Dict, Callable
from openai import OpenAI
import google.generativeai as genai
from tavily import TavilyClient


# API Endpoints
API_CONFIGS = {
    "groq": {
        "prefix": "gsk_",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "supports_tools": True
    },
    "openai": {
        "prefix": "sk-",
        "base_url": None,
        "default_model": "gpt-4o",
        "supports_tools": True
    },
    "xai": {
        "prefix": "xai-",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-2-latest",
        "supports_tools": True
    },
    "gemini": {
        "prefix": "AIza",
        "base_url": None,
        "default_model": "gemini-2.0-flash",
        "supports_tools": False  # Different implementation
    }
}

# Tool definitions for function calling
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current, real-time information about a topic. Use this to find facts, news, data, and evidence to support your analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information"
                }
            },
            "required": ["query"]
        }
    }
}


def detect_api_type(api_key: str) -> Tuple[str, str, bool]:
    """
    Detect API type from key prefix.
    Returns: (api_type, default_model, supports_tools)
    """
    if not api_key or len(api_key) < 10:
        return None, None, False
    
    for api_type, config in API_CONFIGS.items():
        if api_key.startswith(config["prefix"]):
            return api_type, config["default_model"], config["supports_tools"]
    
    return "gemini", "gemini-2.0-flash", False


class UnifiedLLM:
    """
    Unified LLM client with tool calling support.
    Auto-detects provider and enables function calling for research.
    """
    
    def __init__(self, api_key: str, agent_name: str = "Agent", console=None):
        self.api_key = api_key
        self.agent_name = agent_name
        self.console = console
        self.api_type, self.model, self.supports_tools = detect_api_type(api_key)
        self._client = None
        self._gemini_model = None
        self._tavily = None
        
        # Setup Tavily for tool execution
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key:
            self._tavily = TavilyClient(api_key=tavily_key)
        
        if self.api_type:
            self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate client based on API type."""
        if self.api_type == "gemini":
            genai.configure(api_key=self.api_key)
            self._gemini_model = genai.GenerativeModel(self.model)
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
        api_names = {
            "groq": "Groq",
            "openai": "OpenAI",
            "xai": "xAI",
            "gemini": "Gemini"
        }
        tools_status = "✓ Tool Calling" if self.supports_tools else "○ No Tools"
        return f"{api_names.get(self.api_type, 'Unknown')} ({self.model}) [{tools_status}]"
    
    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool call and return the result."""
        if tool_name == "web_search" and self._tavily:
            query = arguments.get("query", "")
            if self.console:
                self.console.print(f"      [cyan]🔍 Searching:[/cyan] [dim]{query}[/dim]")
            
            try:
                response = self._tavily.search(query=query, search_depth="advanced", max_results=3)
                results = []
                for r in response.get("results", [])[:3]:
                    results.append(f"Source: {r['url']}\nContent: {r['content'][:300]}")
                    if self.console:
                        self.console.print(f"      [green]✓ Found:[/green] [dim]{r['url'][:50]}...[/dim]")
                return "\n\n".join(results) if results else "No results found."
            except Exception as e:
                return f"Search failed: {str(e)[:50]}"
        
        return "Tool not available."
    
    def generate_with_tools(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate response with tool calling enabled (LLM decides when to search)."""
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                # Gemini uses different tool calling - fallback to direct research
                if self._tavily:
                    # Do a quick search first for Gemini
                    try:
                        query = prompt[:100]  # Use first part of prompt as search query
                        if self.console:
                            self.console.print(f"      [cyan]🔍 Researching...[/cyan]")
                        response = self._tavily.search(query=query, search_depth="basic", max_results=2)
                        context = ""
                        for r in response.get("results", [])[:2]:
                            context += f"\nSource: {r['url']}\n{r['content'][:200]}\n"
                            if self.console:
                                self.console.print(f"      [green]✓ Found:[/green] [dim]{r['url'][:40]}...[/dim]")
                        full_prompt = f"{system_prompt}\n\nResearch Context:\n{context}\n\n{prompt}"
                    except:
                        full_prompt = f"{system_prompt}\n\n{prompt}"
                else:
                    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                
                response = self._gemini_model.generate_content(full_prompt)
                return response.text.strip()
            
            # OpenAI-compatible APIs with tool calling
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Check if we should use tool calling
            use_tools = self._tavily and self.supports_tools
            
            if use_tools:
                try:
                    # First call - may request tool use
                    response = self._client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=[SEARCH_TOOL],
                        tool_choice="auto"
                    )
                    
                    message = response.choices[0].message
                    
                    # Handle tool calls if any
                    max_tool_iterations = 3
                    iteration = 0
                    
                    while message.tool_calls and iteration < max_tool_iterations:
                        iteration += 1
                        messages.append(message)
                        
                        for tool_call in message.tool_calls:
                            func_name = tool_call.function.name
                            func_args = json.loads(tool_call.function.arguments)
                            
                            if self.console:
                                self.console.print(f"      [yellow]🛠️ Tool Call:[/yellow] {func_name}")
                            
                            result = self._execute_tool(func_name, func_args)
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result
                            })
                        
                        # Continue conversation with tool results
                        response = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            tools=[SEARCH_TOOL],
                            tool_choice="auto"
                        )
                        message = response.choices[0].message
                    
                    return message.content.strip() if message.content else None
                
                except Exception as tool_error:
                    # If tool calling fails, fall back to direct search + generate
                    if self.console:
                        self.console.print(f"      [dim]Fallback to direct research...[/dim]")
                    
                    if self._tavily:
                        try:
                            query = prompt[:100]
                            if self.console:
                                self.console.print(f"      [cyan]🔍 Researching...[/cyan]")
                            response = self._tavily.search(query=query, search_depth="basic", max_results=2)
                            context = ""
                            for r in response.get("results", [])[:2]:
                                context += f"\nSource: {r['url']}\n{r['content'][:200]}\n"
                                if self.console:
                                    self.console.print(f"      [green]✓ Found:[/green] [dim]{r['url'][:40]}...[/dim]")
                            messages[-1]["content"] = f"Research Context:\n{context}\n\n{prompt}"
                        except:
                            pass
                    
                    response = self._client.chat.completions.create(
                        model=self.model,
                        messages=messages
                    )
                    return response.choices[0].message.content.strip()
            else:
                # No tools - direct generation
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content.strip()
        
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]API Error: {str(e)[:50]}[/dim red]")
            return None
    
    def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate a response (without tool calling)."""
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                response = self._gemini_model.generate_content(full_prompt)
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
                self.console.print(f"      [dim red]API Error: {str(e)[:50]}[/dim red]")
            return None
    
    def generate_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate JSON response with tool calling enabled."""
        return self.generate_with_tools(prompt + "\n\nRespond with valid JSON only.", system_prompt)
