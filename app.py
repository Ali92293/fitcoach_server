"""
FitCoach Pro — باكي AI Server
يعمل محلياً وعلى Vercel
"""
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from baaki_brain import BaakiAI

app = Flask(__name__, static_folder="static")
CORS(app)

# ── جلسات في الذاكرة (محلي) أو بدون ذاكرة (Vercel) ──
SESSIONS: dict = {}
SESSION_TIMEOUT = 3600

def get_ai(user_id: str) -> BaakiAI:
    now = time.time()
    expired = [k for k, v in SESSIONS.items() if now - v["created"] > SESSION_TIMEOUT]
    for k in expired:
        del SESSIONS[k]
    if user_id not in SESSIONS:
        SESSIONS[user_id] = {"ai": BaakiAI(), "created": now}
    return SESSIONS[user_id]["ai"]

# ── Routes ──

@app.route("/")
def index():
    return send_from_directory("static", "FitCoach_Pro.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data      = request.get_json(force=True) or {}
        msg       = data.get("message", "").strip()
        user_id   = data.get("user_id", "default")
        user_data = data.get("user_data", {})

        if not msg:
            return jsonify({"error": "الرسالة فارغة"}), 400
        if len(msg) > 500:
            return jsonify({"error": "الرسالة طويلة"}), 400

        ai     = get_ai(user_id)
        result = ai.chat(msg, user_data)

        return jsonify({
            "reply":      result["reply"],
            "intent":     result["intent"],
            "confidence": result["confidence"],
            "turn":       result["turn"],
            "engine":     "baaki-local-v1",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def reset():
    data    = request.get_json(force=True) or {}
    user_id = data.get("user_id", "default")
    if user_id in SESSIONS:
        SESSIONS[user_id]["ai"].reset()
    return jsonify({"status": "ok"})

@app.route("/api/quick-tips", methods=["POST"])
def quick_tips():
    data      = request.get_json(force=True) or {}
    user_data = data.get("user_data", {})
    user_id   = data.get("user_id", "default")
    ai        = get_ai(user_id)
    result    = ai.chat("أعطني نصائح يومية سريعة", user_data)
    return jsonify({"tips": result["reply"]})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status":   "running 🟢",
        "engine":   "baaki-local-v1",
        "sessions": len(SESSIONS),
        "time":     datetime.now().strftime("%H:%M:%S"),
    })

# نقطة الدخول لـ Vercel — يجب أن يكون الـ app معرّفاً في الأعلى
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🏋️  FitCoach Pro — http://127.0.0.1:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
