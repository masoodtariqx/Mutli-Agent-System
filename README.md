# 🎯 Multi-Agent Prediction Battle System

AI agents make predictions on real-world events and debate autonomously.

## ✨ Features

| Feature | Description |
|:---|:---|
| **🔧 Native Function Calling** | OpenAI, Gemini, Grok with tool definitions |
| **💬 Autonomous Debate** | Agents decide to speak, pass, or conclude |
| **🎙️ ElevenLabs Voice** | Distinct voices for each agent |
| **🔌 Multi-API** | Supports OpenAI, xAI (Grok), Gemini, Groq |
| **📊 Beautiful UI** | Rich terminal formatting |

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## 📋 API Configuration

Auto-detects API type from key prefix:

| Key Prefix | Provider | Model | Function Calling |
|:---|:---|:---|:---|
| `sk-` | OpenAI | gpt-4o | ✅ tools + tool_choice |
| `AIza` | Gemini | gemini-2.0-flash | ✅ FunctionDeclaration |
| `xai-` | xAI (Grok) | grok-2-latest | ✅ tools + tool_choice |
| `gsk_` | Groq | llama-3.3-70b | ❌ |

### .env

```env
CHATGPT_KEY=sk-your_openai_key
GROK_KEY=xai-your_grok_key
GEMINI_KEY=AIza_your_gemini_key

# Optional: ElevenLabs for voice
ELEVENLABS_API_KEY=your_key
```

## 🎮 Usage

```bash
python main.py
```

Enter a Polymarket event (ID, URL, or slug), then choose:
- **Mode 1**: Text Debate
- **Mode 2**: Voice Debate (ElevenLabs)

## 🏗️ Architecture

### Native Function Calling Flow

```
1. Send prompt + tool definitions to model
2. Model returns tool_call (function name + args)
3. Execute tool via callback
4. Send result back to model
5. Model generates final response
```

### Supported APIs

- **OpenAI**: `chat.completions.create()` with `tools` param
- **Gemini**: `FunctionDeclaration` + `function_call` response
- **xAI/Grok**: OpenAI-compatible `tools` param
- **JSON**: Native `response_format` / `response_mime_type`

## 🔊 Voice (ElevenLabs)

Each agent has a distinct voice:
- **ChatGPT**: Daniel (calm, professional)
- **Grok**: Liam (energetic, casual)
- **Gemini**: Sarah (analytical)
- **Moderator**: Rachel (neutral)

## 📦 Dependencies

```
openai
google-genai
elevenlabs
rich
pygame
python-dotenv
requests
pydantic
```

## 📄 License

MIT
