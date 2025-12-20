# 🎯 AI Prediction Battle

A multi-agent AI system that researches, predicts, and debates real-world events from **Polymarket**.

Three AI agents (ChatGPT, Grok, Gemini) independently analyze events, make locked predictions, and engage in structured debates.

---

## ✨ Features

| Version | Feature | Description |
|:---:|:---|:---|
| **V0** | Prediction Engine | Independent research & locked predictions |
| **V1** | Text Debate | Natural conversation-style debate |
| **V2** | Voice Debate | Live TTS with unique voices per agent |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file:
```env
# Required (at least one)
OPENAI_API_KEY=sk-your-key      # ChatGPT
XAI_API_KEY=xai-your-key        # Grok
GEMINI_API_KEY=your-key         # Gemini

# Optional (for better research)
TAVILY_API_KEY=tvly-your-key
```

### 3. Run
```bash
python main.py
```

---

## 💻 Usage

### Interactive Mode (Recommended)
```bash
python main.py
```
Prompts for event ID and mode (text/voice).

### Command Line
```bash
# Full battle with text debate
python main.py run <event_id>

# Full battle with voice debate
python main.py run <event_id> --voice

# Predictions only
python main.py predict <event_id>

# Debate existing predictions
python main.py debate <event_id>

# Discover events
python main.py discover
```

### Event Input
Accepts: Event ID, URL, or Slug
```bash
python main.py run 74949
python main.py run https://polymarket.com/event/some-event
python main.py run best-ai-model-2025
```

---

## 🤖 AI Agents

| Agent | API | Strategy |
|:---|:---|:---|
| **ChatGPT** | OpenAI | Precision-focused, official sources |
| **Grok** | xAI | Early signals, social sentiment |
| **Gemini** | Google | Constraints, historical precedents |

---

## 🏗️ Architecture

```
main.py                 ← Entry point
├── src/agents/         ← AI agents (ChatGPT, Grok, Gemini)
├── src/services/       ← Prediction, Debate, Voice services
├── src/utils/          ← Console output, Voice (TTS)
├── src/models.py       ← Data models (Pydantic)
├── src/database.py     ← SQLite storage
└── src/prompts.py      ← Agent prompts
```

---

## 📊 Output

### Predictions (V0)
- YES/NO prediction with probability
- Key claims with sources
- Rationale for prediction
- Stored in SQLite database

### Text Debate (V1)
- Natural back-and-forth conversation
- Agents challenge each other's claims
- Moderator guides discussion

### Voice Debate (V2)
- Unique voice per agent
- Live audio playback
- Same debate flow as V1

---

## 📦 Dependencies

```
python-dotenv
requests
pydantic
google-generativeai
openai
tavily-python
rich
edge-tts
pygame
```

---

## ⚠️ Notes

- **Rate Limits**: Free API tiers have limits. Use paid keys for production.
- **Voice**: Requires audio output. Uses edge-tts (free).
- **Research**: Add `TAVILY_API_KEY` for better web research.

---

## ⚖️ Legal Disclaimer

- This tool is for **informational and research purposes only.**
- It does not represent financial or betting advice.
- No real-money wagering functionality is included.
