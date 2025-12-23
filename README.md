# 🎯 Multi-Agent Prediction Battle System

AI agents make predictions on real-world events and debate autonomously.

## ✨ Features

| Feature | Description |
|:---|:---|
| **� Native Search** | OpenAI web_search + Gemini Search Grounding |
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

| Key Prefix | Provider | Model | Native Search |
|:---|:---|:---|:---|
| `sk-` | OpenAI | gpt-4o | ✅ web_search |
| `AIza` | Gemini | gemini-2.0-flash | ✅ Search Grounding |
| `xai-` | xAI (Grok) | grok-2-latest | ❌ |
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

## 🏗️ System Flow

```
User Input → Polymarket API → Event Details
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
 ChatGPT          Grok           Gemini
 (OpenAI)        (xAI)          (Google)
    ↓               ↓               ↓
 Native          Model          Search
 Search         Knowledge      Grounding
    ↓               ↓               ↓
 YES/NO%        YES/NO%        YES/NO%
    └───────────────┼───────────────┘
                    ↓
          Autonomous Debate
    (Agents decide to speak/pass/end)
                    ↓
           Final Predictions
```

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
