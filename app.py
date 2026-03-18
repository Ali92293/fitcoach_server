import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from baaki_brain import BaakiAI

app = Flask(__name__, static_folder="static")
CORS(app)

# ══════════════════════════════════════════
# تقديم الصفحة الرئيسية
# ══════════════════════════════════════════
@app.route("/")
def index():
    """إرسال ملف index.html من الجذر"""
    return send_from_directory('.', 'index.html')

@app.route("/static/<path:filename>")
def static_files(filename):
    """خدمة ملفات static"""
    return send_from_directory('static', filename)

# ══════════════════════════════════════════
# API Routes
# ══════════════════════════════════════════
YOUTUBE_RESOURCES = {
    "صدر": "https://www.youtube.com/results?search_query=تمرين+صدر+صحيح",
    "ظهر": "https://www.youtube.com/results?search_query=تمرين+ظهر+صحيح",
    "ارجل": "https://www.youtube.com/results?search_query=تمرين+ارجل+صحيح",
    "بايسبس": "https://www.youtube.com/results?search_query=تمرين+بايسبس",
    "بطن": "https://www.youtube.com/results?search_query=تمارين+بطن+للمبتدئين",
    "تخسيس": "https://www.youtube.com/results?search_query=تمارين+حرق+دهون+كارديو"
}

SESSIONS = {}
SESSION_TIMEOUT = 3600

def get_ai(user_id):
    now = time.time()
    expired = [k for k, v in SESSIONS.items() if now - v["created"] > SESSION_TIMEOUT]
    for k in expired:
        del SESSIONS[k]
    if user_id not in SESSIONS:
        SESSIONS[user_id] = {"ai": BaakiAI(), "created": now}
    return SESSIONS[user_id]["ai"]

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True) or {}
        msg = data.get("message", "").strip()
        user_id = data.get("user_id", "default")
        user_data = data.get("user_data", {})

        ai = get_ai(user_id)
        result = ai.chat(msg, user_data)
        reply = result["reply"]

        # إضافة روابط يوتيوب
        found_links = []
        for key, link in YOUTUBE_RESOURCES.items():
            if key in msg:
                found_links.append(f"🎬 فيديو تعليمي لتمارين ({key}):\n{link}")
        if found_links:
            reply += "\n\n" + "═" * 15 + "\n" + "\n\n".join(found_links)

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "running 🟢", "sessions": len(SESSIONS)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)