"""
StressTest AI — Decision Stress Testing for US Stock Traders
Flask backend + Gemini AI integration
"""

import os
import json
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../dashboard", static_url_path="")
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── AI Core ──────────────────────────────────────────────────────────────────

def analyze_trade(trade_idea: str, asset: str, direction: str, timeframe: str) -> dict:
    prompt = f"""You are a professional trading risk analyst specializing in US stocks and tokenized US stocks (rTokens).

A trader wants to make the following trade:
- Asset: {asset}
- Direction: {direction} (buy/long or sell/short)
- Timeframe: {timeframe}
- Trade thesis: {trade_idea}

Your job is to stress test this decision by finding 3 historically similar market scenarios and showing what happened.

Respond ONLY with a valid JSON object in this exact format, no extra text, no markdown:
{{
  "trade_summary": "One sentence summarizing the trade idea",
  "overall_verdict": "SAFE",
  "verdict_reason": "2-3 sentences explaining the overall verdict",
  "risk_score": 45,
  "scenarios": [
    {{
      "title": "Short scenario title",
      "date": "Month Year",
      "similarity": 85,
      "what_happened": "2-3 sentences describing the historical event",
      "outcome": "POSITIVE",
      "return_pct": 8.5,
      "lesson": "One sentence key lesson for the trader"
    }},
    {{
      "title": "Short scenario title",
      "date": "Month Year",
      "similarity": 72,
      "what_happened": "2-3 sentences describing the historical event",
      "outcome": "NEGATIVE",
      "return_pct": -5.2,
      "lesson": "One sentence key lesson for the trader"
    }},
    {{
      "title": "Short scenario title",
      "date": "Month Year",
      "similarity": 65,
      "what_happened": "2-3 sentences describing the historical event",
      "outcome": "MIXED",
      "return_pct": 2.1,
      "lesson": "One sentence key lesson for the trader"
    }}
  ],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "suggested_action": "One concrete recommendation for the trader"
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 1500,
            "temperature": 0.3,
            "responseMimeType": "application/json"
        },
    }

    resp = requests.post(url, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("../dashboard", "index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": "gemini-2.0-flash"})


@app.route("/api/stress-test", methods=["POST"])
def stress_test():
    body = request.get_json()
    if not body:
        return jsonify({"error": "No JSON body"}), 400

    trade_idea = body.get("trade_idea", "").strip()
    asset = body.get("asset", "AAPL").strip()
    direction = body.get("direction", "long").strip()
    timeframe = body.get("timeframe", "1 week").strip()

    if not trade_idea:
        return jsonify({"error": "trade_idea is required"}), 400

    try:
        result = analyze_trade(trade_idea, asset, direction, timeframe)
        result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result["input"] = {
            "trade_idea": trade_idea,
            "asset": asset,
            "direction": direction,
            "timeframe": timeframe,
        }

        out_path = os.path.join(BASE_DIR, "examples", "sample_output", "latest_analysis.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        return jsonify(result)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI response parse error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/demo", methods=["GET"])
def demo():
    demo_path = os.path.join(BASE_DIR, "examples", "sample_output", "demo_analysis.json")
    with open(demo_path) as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n🧠 StressTest AI running on http://localhost:{port}")
    print(f"   POST /api/stress-test  — analyze a trade idea")
    print(f"   GET  /api/demo         — demo without API key")
    print(f"   GET  /health\n")
    app.run(host="0.0.0.0", port=port, debug=False)
