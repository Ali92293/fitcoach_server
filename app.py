"""
╔══════════════════════════════════════════════════════════╗
║         FitCoach Pro — سيرفر باكي AI                    ║
║         يعمل بالكامل بدون أي API خارجي                  ║
║         نسخة متكاملة للنشر على Vercel                   ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from baaki_brain import BaakiAI

# ══════════════════════════════════════════
# إعداد Flask
# ══════════════════════════════════════════
app = Flask(__name__, static_folder="static")
CORS(app)

# ══════════════════════════════════════════
# قاعدة بيانات الروابط التعليمية (YouTube)
# ══════════════════════════════════════════
YOUTUBE_RESOURCES = {
    "صدر": "https://www.youtube.com/results?search_query=تمرين+صدر+صحيح",
    "ظهر": "https://www.youtube.com/results?search_query=تمرين+ظهر+صحيح",
    "ارجل": "https://www.youtube.com/results?search_query=تمرين+ارجل+صحيح",
    "بايسبس": "https://www.youtube.com/results?search_query=تمرين+بايسبس",
    "ترايسبس": "https://www.youtube.com/results?search_query=تمرين+ترايسبس",
    "بطن": "https://www.youtube.com/results?search_query=تمارين+بطن+للمبتدئين",
    "تخسيس": "https://www.youtube.com/results?search_query=تمارين+حرق+دهون+كارديو",
    "تضخيم": "https://www.youtube.com/results?search_query=نظام+غذائي+للتضخيم"
}

# ══════════════════════════════════════════
# إدارة الجلسات
# ══════════════════════════════════════════
SESSIONS: dict = {}
SESSION_TIMEOUT = 3600  # ساعة

def get_ai(user_id: str) -> BaakiAI:
    """إرجاع نموذج AI للمستخدم أو إنشاء جديد"""
    now = time.time()

    # حذف الجلسات القديمة
    expired = [k for k, v in SESSIONS.items()
               if now - v["created"] > SESSION_TIMEOUT]
    for k in expired:
        del SESSIONS[k]
        print(f"🗑  حُذفت جلسة: {k}")

    if user_id not in SESSIONS:
        SESSIONS[user_id] = {"ai": BaakiAI(), "created": now}
        print(f"✨ جلسة جديدة: {user_id}")

    return SESSIONS[user_id]["ai"]

# ══════════════════════════════════════════
# تقديم الصفحة الرئيسية
# ══════════════════════════════════════════
@app.route("/")
def index():
    """إرسال ملف index.html من الجذر"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        return f"خطأ في تحميل الصفحة: {str(e)}", 500

@app.route("/static/<path:filename>")
def static_files(filename):
    """خدمة ملفات static"""
    try:
        return send_from_directory('static', filename)
    except Exception as e:
        return f"خطأ في تحميل الملف: {str(e)}", 404

# ══════════════════════════════════════════
# API Routes
# ══════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def chat():
    t0 = time.time()
    try:
        data = request.get_json(force=True) or {}
        msg = data.get("message", "").strip()
        user_id = data.get("user_id", "default")
        user_data = data.get("user_data", {})

        if not msg:
            return jsonify({"error": "الرسالة فارغة"}), 400
        if len(msg) > 500:
            return jsonify({"error": "الرسالة طويلة جداً"}), 400

        print(f"💬 [{user_id[:8]}] ← {msg[:60]}")

        ai = get_ai(user_id)
        result = ai.chat(msg, user_data)
        
        # الحصول على الرد من محرك باكي المحلي
        reply = result["reply"]

        # --- إضافة روابط اليوتيوب تلقائياً ---
        found_links = []
        for key, link in YOUTUBE_RESOURCES.items():
            if key in msg:
                found_links.append(f"🎬 فيديو تعليمي لتمارين ({key}):\n{link}")
        
        if found_links:
            reply += "\n\n" + "═" * 15 + "\n" + "\n\n".join(found_links)

        elapsed = round(time.time() - t0, 3)

        print(f"✅ [{user_id[:8]}] intent={result['intent']} ({elapsed}s)")

        return jsonify({
            "reply": reply,
            "intent": result["intent"],
            "confidence": result["confidence"],
            "turn": result["turn"],
            "latency_s": elapsed,
            "engine": "baaki-local-v1",
        })

    except Exception as e:
        print(f"❌ خطأ: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json(force=True) or {}
    user_id = data.get("user_id", "default")
    if user_id in SESSIONS:
        SESSIONS[user_id]["ai"].reset()
        print(f"🔄 إعادة محادثة: {user_id}")
    return jsonify({"status": "ok"})


@app.route("/api/quick-tips", methods=["POST"])
def quick_tips():
    """نصائح يومية مخصصة بدون API"""
    data = request.get_json(force=True) or {}
    user_data = data.get("user_data", {})
    user_id = data.get("user_id", "default")

    ai = get_ai(user_id)
    result = ai.chat("أعطني نصائح يومية سريعة", user_data)

    return jsonify({"tips": result["reply"]})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running 🟢",
        "engine": "baaki-local-v1 (no external API)",
        "sessions": len(SESSIONS),
        "time": datetime.now().strftime("%H:%M:%S"),
    })

# ══════════════════════════════════════════
# تشغيل السيرفر
# ══════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"""
╔══════════════════════════════════════════════════╗
║    🏋️  FitCoach Pro — باكي AI (جاهز للنشر)  ✅    ║
╠══════════════════════════════════════════════════╣
║  📁 الملفات:                                     ║
║     - index.html في الجذر                        ║
║     - static/ مجلد للملفات الثابتة               ║
║  🌐 الموقع:   http://0.0.0.0:{port}             ║
╚══════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=port, debug=False)