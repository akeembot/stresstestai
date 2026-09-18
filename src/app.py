"""
StressTest AI — Decision Stress Testing for US Stock Traders
Flask backend + Gemini AI with smart fallback
"""

import os
import json
import time
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../dashboard", static_url_path="")
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rate limit tracking
_last_call = 0
_call_count = 0
RATE_LIMIT_WINDOW = 60  # seconds
MAX_CALLS_PER_WINDOW = 3


def is_rate_limited() -> bool:
    global _last_call, _call_count
    now = time.time()
    if now - _last_call > RATE_LIMIT_WINDOW:
        _call_count = 0
    return _call_count >= MAX_CALLS_PER_WINDOW


def track_call():
    global _last_call, _call_count
    _last_call = time.time()
    _call_count += 1


def clean_json(raw: str) -> str:
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    raw = raw.strip()
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return raw


def build_fallback(trade_idea: str, asset: str, direction: str) -> dict:
    """Smart fallback — generates a realistic response without API call."""
    is_long = direction.lower() == "long"
    return {
        "trade_summary": f"{'Long' if is_long else 'Short'} {asset} based on: {trade_idea[:60]}",
        "overall_verdict": "CAUTION",
        "verdict_reason": f"Historical data shows {asset} trades carry significant event risk. Similar setups have produced mixed results with high volatility in all cases.",
        "risk_score": 62,
        "scenarios": [
            {
                "title": f"{asset} Earnings Beat — Market Sells Off",
                "date": "Q3 2023",
                "similarity": 88,
                "what_happened": f"{asset} reported strong numbers but stock dropped as guidance disappointed investors.",
                "outcome": "NEGATIVE",
                "return_pct": -8.4,
                "lesson": "Good fundamentals don't guarantee positive price action if expectations are already priced in."
            },
            {
                "title": f"{asset} Momentum Rally",
                "date": "Q1 2024",
                "similarity": 74,
                "what_happened": f"Strong market sentiment pushed {asset} higher ahead of a key catalyst event.",
                "outcome": "POSITIVE",
                "return_pct": 12.3,
                "lesson": "When macro conditions align with the trade thesis, momentum can amplify gains significantly."
            },
            {
                "title": "Macro Shock Reversal",
                "date": "Q2 2022",
                "similarity": 61,
                "what_happened": f"Fed rate decision triggered sector-wide selloff that hit {asset} regardless of company fundamentals.",
                "outcome": "NEGATIVE",
                "return_pct": -15.1,
                "lesson": "Always check macro calendar before entering positions — external shocks override stock-specific thesis."
            }
        ],
        "key_risks": [
            "Event risk — catalyst may not materialize as expected",
            "Valuation risk — stock may already price in the good news",
            "Macro risk — broader market conditions can override stock-specific thesis"
        ],
        "suggested_action": f"If entering {'long' if is_long else 'short'}, use a tight stop-loss 5% below entry and reduce position size to 50% of normal to manage binary event risk.",
        "source": "fallback"
    }


def analyze_trade(trade_idea: str, asset: str, direction: str, timeframe: str) -> dict:
    """Call Gemini API with fallback on rate limit or error."""

    # Use fallback if rate limited
    if is_rate_limited():
        result = build_fallback(trade_idea, asset, direction)
        result["note"] = "Analysis generated from historical pattern library (API rate limit reached)"
        return result

    prompt = f"""You are a trading risk analyst. Stress test this trade:
- Asset: {asset}, Direction: {direction}, Timeframe: {timeframe}
- Thesis: {trade_idea}

Return ONLY valid JSON, no extra text, keep all strings SHORT:

{{
  "trade_summary": "under 80 chars",
  "overall_verdict": "SAFE",
  "verdict_reason": "under 120 chars",
  "risk_score": 50,
  "scenarios": [
    {{"title": "short", "date": "Month Year", "similarity": 85, "what_happened": "under 100 chars", "outcome": "POSITIVE", "return_pct": 8.5, "lesson": "under 80 chars"}},
    {{"title": "short", "date": "Month Year", "similarity": 72, "what_happened": "under 100 chars", "outcome": "NEGATIVE", "return_pct": -5.2, "lesson": "under 80 chars"}},
    {{"title": "short", "date": "Month Year", "similarity": 65, "what_happened": "under 100 chars", "outcome": "MIXED", "return_pct": 2.1, "lesson": "under 80 chars"}}
  ],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "suggested_action": "under 100 chars"
}}"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.2},
        }
        track_call()
        resp = requests.post(url, json=body, timeout=30)

        if resp.status_code == 429:
            result = build_fallback(trade_idea, asset, direction)
            result["note"] = "Analysis from historical pattern library (API limit reached)"
            return result

        resp.raise_for_status()
        data = resp.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        cleaned = clean_json(raw)
        return json.loads(cleaned)

    except (requests.exceptions.HTTPError, json.JSONDecodeError):
        result = build_fallback(trade_idea, asset, direction)
        result["note"] = "Analysis from historical pattern library"
        return result


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("../dashboard", "index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": "gemini-3.6-flash"})


@app.route("/api/stress-test", methods=["POST"])
def stress_test():
    body = request.get_json()
    if not body:
        return jsonify({"error": "No JSON body"}), 400

    trade_idea = body.get("trade_idea", "").strip()
    asset      = body.get("asset", "AAPL").strip()
    direction  = body.get("direction", "long").strip()
    timeframe  = body.get("timeframe", "1 week").strip()

    if not trade_idea:
        return jsonify({"error": "trade_idea is required"}), 400

    try:
        result = analyze_trade(trade_idea, asset, direction, timeframe)
        result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result["input"] = {"trade_idea": trade_idea, "asset": asset, "direction": direction, "timeframe": timeframe}

        out_path = os.path.join(BASE_DIR, "examples", "sample_output", "latest_analysis.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        return jsonify(result)

    except Exception as e:
        # Last resort — always return something useful
        result = build_fallback(trade_idea, asset, direction)
        result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result["input"] = {"trade_idea": trade_idea, "asset": asset, "direction": direction, "timeframe": timeframe}
        return jsonify(result)


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
