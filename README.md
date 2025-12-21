# 🎯 Multi-Agent Prediction Battle System

AI agents collaborate and debate to make predictions on real-world events.

## ✨ Key Features

| Feature | Description |
|:---|:---|
| **🛠️ Tool Calling** | LLM decides when to search using function calling |
| **💬 Natural Debate** | Free-flowing conversation like real experts |
| **🎙️ Voice Output** | Agents speak with unique voices |
| **🔌 Multi-API** | Supports Groq, OpenAI, xAI, Gemini |
| **📊 Beautiful UI** | Rich terminal formatting |

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Run interactive mode
python main.py
```

## 📋 API Configuration

The system **auto-detects** API type from key prefix:

| Key Prefix | Provider | Model |
|:---|:---|:---|
| `gsk_` | Groq (FREE) | llama-3.3-70b |
| `sk-` | OpenAI | gpt-4o |
| `xai-` | xAI | grok-2-latest |
| `AIza` | Gemini | gemini-2.0-flash |

### .env Example

```env
# Agents (use any compatible API)
CHATGPT_GROQ_KEY=gsk_your_key
GROK_GROQ_KEY=gsk_your_key  
GEMINI_GROQ_KEY=gsk_your_key

# Research (enables tool calling)
TAVILY_API_KEY=tvly_your_key
```

## 🎮 Usage

### Interactive Mode
```bash
python main.py
```

### Commands
```bash
# Full battle (prediction + debate)
python main.py run <event_id>

# With voice (agents speak)
python main.py run <event_id> --voice

# Prediction only
python main.py predict <event_id>

# Discover events
python main.py discover
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Input                        │
│               (Event ID/URL/Slug)                   │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Polymarket API                         │
│           Fetch Event Details                       │
└─────────────────────┬───────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
│ChatGPT │      │   Grok    │     │  Gemini   │
│ Agent  │      │   Agent   │     │  Agent    │
└───┬────┘      └─────┬─────┘     └─────┬─────┘
    │                 │                 │
    │    🛠️ Tool Calling: web_search    │
    │    🔍 LLM decides when to search  │
    │                 │                 │
┌───▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
│ YES/NO │      │  YES/NO   │     │  YES/NO   │
│   %    │      │    %      │     │    %      │
└───┬────┘      └─────┬─────┘     └─────┬─────┘
    │                 │                 │
    └─────────────────┼─────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Natural Debate                         │
│       Free-flowing expert discussion                │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│             Final Summary                           │
│          Locked Predictions                         │
└─────────────────────────────────────────────────────┘
```

## 📦 Dependencies

```
python-dotenv
requests
pydantic
google-generativeai
tavily-python
rich
edge-tts
pygame
openai
```

## 📄 License

MIT
