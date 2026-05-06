# ♻️ PlasticBot — Plastics-Only Recycling Chatbot

A Python terminal chatbot for office plastics recycling guidance,
powered by the Claude AI API and your own CSV data files.

## Project structure

```
plasticbot/
├── chatbot.py        ← main entry point (run this)
├── data_loader.py    ← reads the two CSV files
├── matcher.py        ← intent detection + keyword scoring
├── api_client.py     ← Claude API call (set your URL here)
├── reporter.py       ← issue record creation + logging
├── data/
│   ├── recycling_rules_plastics_only.csv
│   └── recycling_faq_plastics_only.csv
└── README.md
```

## Setup

1. **Python 3.10+** required (no third-party packages needed — stdlib only).

2. **Set your API endpoint** in `api_client.py`:
   ```python
   API_URL = "INSERT API LINK HERE"   # ← replace this line
   ```

3. **Run the chatbot:**
   ```bash
   python chatbot.py
   ```

## How it works (follows the system flowchart)

```
Employee types question
        │
        ▼
  Detect intent
  ┌─────┼──────────┐
  ▼     ▼          ▼
Disposal FAQ     Report issue
  │       │          │
  ▼       ▼          ▼
Search  Search   Create issue
rules   faq.csv  record +
.csv             notify team
  │       │
  └───┬───┘
      ▼
Send context to Claude API
      ▼
 Return clear answer
      ▼
Collect feedback (👍/👎)
      ▼
Improve rules database
```

## Commands (at the prompt)

| Command | Action |
|---|---|
| *(any question)* | Ask about an item or policy |
| `report issue` | Log a bin problem interactively |
| `history` | Show issues reported this session |
| `exit` | Quit |

## Extending

- **Add rules/FAQs** — just add rows to the CSV files; no code change needed.
- **Persist issues** — replace the in-memory list in `reporter.py` with a DB write or email call.
- **Swap the AI model** — change `MODEL` in `api_client.py`.
