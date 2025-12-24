import os
import json
from typing import Optional, Tuple, Dict, List, Callable
from openai import OpenAI
from google import genai
from google.genai import types


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
        "has_function_calling": True
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


def detect_api_type(api_key: str) -> Tuple[str, str, bool]:
    if not api_key or len(api_key) < 10:
        return None, None, False
    
    for api_type, config in API_CONFIGS.items():
        if api_key.startswith(config["prefix"]):
            return api_type, config["default_model"], config["has_function_calling"]
    
    return "groq", "llama-3.3-70b-versatile", False


class UnifiedLLM:
    
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
        status = "Function Calling" if self.has_function_calling else "No Tools"
        return f"{api_names.get(self.api_type, 'Unknown')} ({self.model}) [{status}]"
    
    def generate_with_tools(
        self, 
        prompt: str, 
        system_prompt: str = "", 
        tools: List[Dict] = None,
        tool_executor: Callable[[str, Dict], str] = None
    ) -> Optional[str]:
        if not self.is_valid():
            return None
        
        if not tools:
            return self.generate(prompt, system_prompt)
        
        try:
            if self.api_type == "gemini":
                return self._gemini_function_call(prompt, system_prompt, tools, tool_executor)
            elif self.api_type in ["openai", "xai"]:
                return self._openai_function_call(prompt, system_prompt, tools, tool_executor)
            else:
                return self.generate(prompt, system_prompt)
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]Tool Error: {str(e)[:80]}[/dim red]")
            return None
    
    def _openai_function_call(
        self, 
        prompt: str, 
        system_prompt: str, 
        tools: List[Dict],
        tool_executor: Callable[[str, Dict], str] = None
    ) -> Optional[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls and tool_executor:
            messages.append(message)
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if self.console:
                    self.console.print(f"      [cyan]Tool call:[/cyan] {function_name}({function_args})")
                
                result = tool_executor(function_name, function_args)
                
                if self.console:
                    self.console.print(f"      [green]Tool result:[/green] {str(result)[:50]}...")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            
            final_response = self._client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return final_response.choices[0].message.content.strip()
        
        return message.content.strip() if message.content else None
    
    def _gemini_function_call(
        self, 
        prompt: str, 
        system_prompt: str, 
        tools: List[Dict],
        tool_executor: Callable[[str, Dict], str] = None
    ) -> Optional[str]:
        function_declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                fn = tool["function"]
                params = fn.get("parameters", {})
                
                properties = {}
                for prop_name, prop_def in params.get("properties", {}).items():
                    prop_type = prop_def.get("type", "string").upper()
                    gemini_type = getattr(types.Type, prop_type, types.Type.STRING)
                    properties[prop_name] = types.Schema(
                        type=gemini_type,
                        description=prop_def.get("description", "")
                    )
                
                declaration = types.FunctionDeclaration(
                    name=fn["name"],
                    description=fn.get("description", ""),
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties=properties,
                        required=params.get("required", [])
                    )
                )
                function_declarations.append(declaration)
        
        gemini_tools = types.Tool(function_declarations=function_declarations)
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = self._gemini_client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(tools=[gemini_tools])
        )
        
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call and tool_executor:
                    fc = part.function_call
                    function_name = fc.name
                    function_args = dict(fc.args) if fc.args else {}
                    
                    if self.console:
                        self.console.print(f"      [cyan]Tool call:[/cyan] {function_name}({function_args})")
                    
                    result = tool_executor(function_name, function_args)
                    
                    if self.console:
                        self.console.print(f"      [green]Tool result:[/green] {str(result)[:50]}...")
                    
                    function_response = types.Part.from_function_response(
                        name=function_name,
                        response={"result": result}
                    )
                    
                    contents = [
                        types.Content(role="user", parts=[types.Part.from_text(full_prompt)]),
                        types.Content(role="model", parts=[part]),
                        types.Content(role="user", parts=[function_response])
                    ]
                    
                    final_response = self._gemini_client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(tools=[gemini_tools])
                    )
                    return final_response.text.strip()
        
        return response.text.strip() if hasattr(response, 'text') else None
    
    def generate_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                return self._gemini_json(prompt, system_prompt)
            elif self.api_type in ["openai", "xai"]:
                return self._openai_json(prompt, system_prompt)
            else:
                return self.generate(prompt, system_prompt)
        except Exception as e:
            if self.console:
                self.console.print(f"      [dim red]JSON Error: {str(e)[:80]}[/dim red]")
            return None
    
    def _openai_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content.strip()
    
    def _gemini_json(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = self._gemini_client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return response.text.strip()
    
    def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        if not self.is_valid():
            return None
        
        try:
            if self.api_type == "gemini":
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
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
    
    def generate_with_search(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        return self.generate(prompt, system_prompt)
