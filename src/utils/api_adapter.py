"""
Unified LLM API Adapter with NATIVE Function Calling for all providers.

Implements proper tool/function calling (NOT search grounding or prompt injection):
- OpenAI: tools parameter with function definitions + responses API
- Gemini: FunctionDeclaration with function_calls handling  
- Grok/xAI: tools parameter with function definitions (OpenAI-compatible)
- Groq: No native function calling, falls back to standard generation
"""

import os
import json
import requests
from typing import Optional, Tuple, Dict, Any, List
from openai import OpenAI
from google import genai
from google.genai import types


# API Configuration
API_CONFIGS = {
    "groq": {
        "prefix": "gsk_",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "has_function_calling": False
    },
    "xai": {
        "prefix": "xai-",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-2-latest",
        "has_function_calling": True  # FIXED: xAI supports function calling
    },
    "gemini": {
        "prefix": "AIza",
        "base_url": None,
        "default_model": "gemini-2.0-flash",
        "has_function_calling": True
    },
    "openai": {
        "prefix": "sk-",
        "base_url": None,
        "default_model": "gpt-4o",
        "has_function_calling": True
    }
}


# Define the web search function schema (used by all APIs that support function calling)
WEB_SEARCH_FUNCTION = {
    "name": "web_search",
    "description": "Search the web for current information about a topic. Use this when you need up-to-date information, news, statistics, or facts.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up"
            }
        },
        "required": ["query"]
    }
}


def detect_api_type(api_key: str) -> Tuple[str, str, bool]:
    """Detect API type from key prefix and return (type, model, has_function_calling)."""
    if not api_key or len(api_key) < 10:
        return None, None, False
    
    for api_type, config in API_CONFIGS.items():
        if api_key.startswith(config["prefix"]):
            return api_type, config["default_model"], config["has_function_calling"]
    
    return "groq", "llama-3.3-70b-versatile", False


def execute_web_search(query: str, tavily_key: str = None) -> str:
    """Execute actual web search using Tavily API or fallback."""
    tavily_key = tavily_key or os.getenv("TAVILY_API_KEY")
    
    if tavily_key:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 5
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results = []
                for r in data.get("results", [])[:3]:
                    results.append(f"- {r.get('title', 'N/A')}: {r.get('content', '')[:200]}")
                return f"Search results for '{query}':\n" + "\n".join(results)
        except Exception:
            pass
    
    # Fallback: return a notice that search was requested but no API available
    return f"[Web search requested for: '{query}' - No search API configured]"


class UnifiedLLM:
    """Unified LLM client with NATIVE function calling support."""
    
    def __init__(self, api_key: str, agent_name: str = "Agent", console=None):
        self.api_key = api_key
        self.agent_name = agent_name
        self.console = console
        self.api_type, self.model, self.has_function_calling = detect_api_type(api_key)
        self._client = None
        self._gemini_client = None
        
        if self.api_type:
            self._setup_client()
    
    def _setup_client(self):
        """Initialize the appropriate API client."""
        if self.api_type == "gemini":
            self._gemini_client = genai.Client(api_key=self.api_key)
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
        tool_status = "Function Calling" if self.has_function_calling else "No Tools"
        return f"{api_names.get(self.api_type, 'Unknown')} ({self.model}) [{tool_status}]"
    
    # =========================================================================
    # NATIVE FUNCTION CALLING IMPLEMENTATION
    # =========================================================================
    
    def generate_with_tools(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Generate response using NATIVE function/tool calling.
        
        This properly implements the function calling loop:
        1. Send prompt with tool definitions
        2. If model returns tool_call, execute the function
        3. Send function result back to model
        4. Get final response
        """
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                return self._generate_gemini_with_function_calling(prompt, system_prompt)
            elif self.api_type == "openai":
                return self._generate_openai_with_function_calling(prompt, system_prompt)
            elif self.api_type == "xai":
                return self._generate_xai_with_function_calling(prompt, system_prompt)
            else:
                # Groq doesn't support function calling, use regular generation
                return self.generate(prompt, system_prompt)
        
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]API Error: {str(e)[:80]}[/dim red]")
            return None
    
    def _generate_openai_with_function_calling(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        OpenAI native function calling using chat.completions with tools parameter.
        """
        if self.console:
            self.console.print(f"      [cyan]Using OpenAI function calling...[/cyan]")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        tools = [{
            "type": "function",
            "function": WEB_SEARCH_FUNCTION
        }]
        
        # First call: let model decide if it needs to use tools
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Check if model wants to call a function
        if assistant_message.tool_calls:
            # Add assistant's response to messages
            messages.append(assistant_message)
            
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if self.console:
                    self.console.print(f"      [green]Tool call:[/green] {function_name}({function_args})")
                
                # Execute the function
                if function_name == "web_search":
                    result = execute_web_search(function_args.get("query", ""))
                else:
                    result = f"Unknown function: {function_name}"
                
                # Add function result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            
            # Second call: get final response with function results
            final_response = self._client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return final_response.choices[0].message.content.strip()
        
        # No tool calls, return direct response
        return assistant_message.content.strip() if assistant_message.content else None
    
    def _generate_xai_with_function_calling(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        xAI/Grok native function calling using tools parameter (OpenAI-compatible).
        """
        if self.console:
            self.console.print(f"      [cyan]Using Grok function calling...[/cyan]")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        tools = [{
            "type": "function",
            "function": WEB_SEARCH_FUNCTION
        }]
        
        # First call: let model decide if it needs to use tools
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Check if model wants to call a function
        if assistant_message.tool_calls:
            messages.append(assistant_message)
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if self.console:
                    self.console.print(f"      [green]Tool call:[/green] {function_name}({function_args})")
                
                if function_name == "web_search":
                    result = execute_web_search(function_args.get("query", ""))
                else:
                    result = f"Unknown function: {function_name}"
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            
            final_response = self._client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return final_response.choices[0].message.content.strip()
        
        return assistant_message.content.strip() if assistant_message.content else None
    
    def _generate_gemini_with_function_calling(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Gemini NATIVE function calling using FunctionDeclaration (NOT search grounding).
        
        Implements proper function calling loop:
        1. Define function with FunctionDeclaration
        2. Model returns function_call if needed
        3. Execute function and return FunctionResponse
        4. Get final response
        """
        if self.console:
            self.console.print(f"      [cyan]Using Gemini function calling...[/cyan]")
        
        # Define the function using Gemini's FunctionDeclaration
        web_search_declaration = types.FunctionDeclaration(
            name="web_search",
            description="Search the web for current information about a topic. Use this when you need up-to-date information, news, statistics, or facts.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query to look up"
                    )
                },
                required=["query"]
            )
        )
        
        # Create Tool with the function declaration
        tools = types.Tool(function_declarations=[web_search_declaration])
        
        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
        
        # First call: let model decide if it needs to call functions
        response = self._gemini_client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(tools=[tools])
        )
        
        # Check if model returned a function call
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = dict(function_call.args) if function_call.args else {}
                    
                    if self.console:
                        self.console.print(f"      [green]Tool call:[/green] {function_name}({function_args})")
                    
                    # Execute the function
                    if function_name == "web_search":
                        result = execute_web_search(function_args.get("query", ""))
                    else:
                        result = f"Unknown function: {function_name}"
                    
                    # Create function response
                    function_response = types.Part.from_function_response(
                        name=function_name,
                        response={"result": result}
                    )
                    
                    # Build conversation with function call and response
                    contents = [
                        types.Content(role="user", parts=[types.Part.from_text(full_prompt)]),
                        types.Content(role="model", parts=[part]),
                        types.Content(role="user", parts=[function_response])
                    ]
                    
                    # Second call: get final response with function result
                    final_response = self._gemini_client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(tools=[tools])
                    )
                    return final_response.text.strip()
        
        # No function call, return direct response
        return response.text.strip()
    
    # =========================================================================
    # NATIVE STRUCTURED OUTPUTS (JSON)
    # =========================================================================
    
    def generate_json(self, prompt: str, system_prompt: str = "", schema: Dict = None) -> Optional[str]:
        """
        Generate JSON using NATIVE structured output parameters (NOT prompt injection).
        
        - OpenAI: response_format={"type": "json_object"}
        - Gemini: response_mime_type="application/json" 
        - Others: Falls back to prompt-based JSON (with clear indication)
        """
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "openai":
                return self._generate_openai_json(prompt, system_prompt)
            elif self.api_type == "gemini":
                return self._generate_gemini_json(prompt, system_prompt)
            elif self.api_type == "xai":
                return self._generate_xai_json(prompt, system_prompt)
            else:
                # Groq: use prompt-based JSON (clearly documented as fallback)
                return self._generate_prompt_json(prompt, system_prompt)
        
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]JSON Error: {str(e)[:80]}[/dim red]")
            return None
    
    def _generate_openai_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """OpenAI native JSON mode using response_format parameter."""
        messages = []
        json_system = (system_prompt + "\n\nYou must respond with valid JSON.") if system_prompt else "You must respond with valid JSON."
        messages.append({"role": "system", "content": json_system})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}  # NATIVE JSON MODE
        )
        return response.choices[0].message.content.strip()
    
    def _generate_xai_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """xAI native JSON mode using response_format parameter (OpenAI-compatible)."""
        messages = []
        json_system = (system_prompt + "\n\nYou must respond with valid JSON.") if system_prompt else "You must respond with valid JSON."
        messages.append({"role": "system", "content": json_system})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}  # NATIVE JSON MODE
        )
        return response.choices[0].message.content.strip()
    
    def _generate_gemini_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Gemini native JSON mode using response_mime_type parameter."""
        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
        
        response = self._gemini_client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"  # NATIVE JSON MODE
            )
        )
        return response.text.strip()
    
    def _generate_prompt_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Fallback: prompt-based JSON for APIs without native support."""
        full_prompt = prompt + "\n\nRespond with valid JSON only, no additional text."
        return self.generate(full_prompt, system_prompt)
    
    # =========================================================================
    # STANDARD GENERATION (No tools)
    # =========================================================================
    
    def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Standard text generation without tools."""
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
    
    # Legacy alias for backwards compatibility
    def generate_with_search(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Alias for generate_with_tools (backwards compatibility)."""
        return self.generate_with_tools(prompt, system_prompt)
