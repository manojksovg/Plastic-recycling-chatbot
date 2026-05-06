# PlasticBot Web Add-on

These files turn your existing terminal PlasticBot into a website.

## What to copy into your project

Copy these into the same folder as your existing `chatbot.py`, `data_loader.py`, `matcher.py`, and `reporter.py`.

```text
plasticbot/
├── webapp.py                  NEW
├── api_client.py              REPLACE existing file
├── templates/                 NEW FOLDER
│   ├── index.html             NEW
│   └── report.html            NEW
├── data/
│   ├── recycling_rules_plastics_only.csv
│   └── recycling_faq_plastics_only.csv
```

## Run the website

```bash
pip install flask
python webapp.py
```

Then open:

```text
http://127.0.0.1:5000
```

## DeepSeek setup

The corrected API endpoint is:

```python
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
```

For safer use, set your key as an environment variable instead of hardcoding it.

Windows PowerShell:

```powershell
setx DEEPSEEK_API_KEY "your-api-key-here"
```

Then restart your terminal and run:

```bash
python webapp.py
```

## Plastics-only clarification

This assistant is not a general recycling chatbot. It is for a plastics-only office recycling bin.

The correct default rule is:

```text
Only eligible plastic items that are empty, clean, and dry should go into this bin.
Paper, metal, glass, food waste, liquids, tissue, e-waste, textiles, and styrofoam should not go into this bin.
```

Bloobin is used only as inspiration for friendly, behaviour-change messaging such as checking, cleaning, and preventing contamination.
