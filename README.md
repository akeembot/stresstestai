# 🧠 StressTest AI — Trade Decision Stress Tester

> **Before you risk real money — see what history says.**

StressTest AI is an AI-powered research tool for US stock traders. Describe your trade idea in plain English, and the AI instantly finds 3 historically similar market scenarios, shows you what happened, and gives you a risk verdict — all before you execute.

Built for the **Bitget AI Base Camp Hackathon S2** · Track 3 — AI Trading Desk · Decision Stress Testing

---

## Demo

▶ [Watch 3-min Demo Video](#) <!-- add before submitting -->

---

## How It Works

```
Trader types idea → AI finds 3 similar historical scenarios → Risk score + verdict + suggested action
```

**Example input:**
> "NVDA is about to report earnings and AI demand is still strong. I want to buy before the report expecting a 10%+ move up."

**Output:**

| Scenario | Date | Similarity | Return | Outcome |
|----------|------|-----------|--------|---------|
| NVDA Q2 2023 Earnings Beat | Aug 2023 | 91% | +8.5% | POSITIVE |
| NVDA Q3 2024 Buy the Rumor | Nov 2024 | 78% | -2.5% | NEGATIVE |
| Meta AI Capex Surprise | Apr 2024 | 65% | -15.1% | NEGATIVE |

**Verdict: CAUTION (62/100)** — Monitor closely, define your risk with options.

---

## Quick Start

**Demo mode (no API key needed):**
```bash
git clone https://github.com/YOUR_USERNAME/stresstestai
cd stresstestai
pip install -r requirements.txt
python src/app.py
# Open dashboard/index.html in browser
# Click "Load demo"
```

**Live mode (with Claude API):**
```bash
cp .env.example .env
# Add your Anthropic API key to .env
python src/app.py
# Open dashboard/index.html → type any trade idea → Run Stress Test
```

---

## API

```bash
POST /api/stress-test
{
  "trade_idea": "Buy NVDA before earnings",
  "asset": "NVDA",
  "direction": "long",
  "timeframe": "1 week"
}

GET /api/demo     # pre-built demo, no API key needed
GET /health
```

**Any agent can integrate in one line:**
```python
import requests
analysis = requests.post('http://localhost:5000/api/stress-test', json={
  "trade_idea": "Buy NVDA before earnings",
  "asset": "NVDA", "direction": "long", "timeframe": "1 week"
}).json()

if analysis['risk_score'] > 60:
    print("High risk — check scenarios before executing")
```

---

## Role of AI (Claude)

Claude (`claude-sonnet-4-6`) is the core decision engine:
- Interprets the trader's natural language trade idea
- Identifies historically similar macro/earnings/sentiment scenarios
- Calculates similarity scores and return outcomes
- Generates risk verdict, key risks, and suggested action

The LLM is not just a chatbot — it acts as a structured research analyst, outputting machine-readable JSON that drives the entire dashboard.

---

## Project Structure

```
stresstestai/
├── src/
│   └── app.py               # Flask backend + Claude AI integration
├── dashboard/
│   └── index.html           # Interactive dashboard (no build step)
├── examples/
│   └── sample_output/
│       └── demo_analysis.json   # Pre-built demo output
├── .env.example
├── requirements.txt
└── README.md
```

---

## Track

**Track 3 — AI Trading Desk** · Sub-theme: **Decision Stress Testing**
Bitget AI Base Camp Hackathon S2

---

## License

MIT
