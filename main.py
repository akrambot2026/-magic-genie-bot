import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "akram12345"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

CHARACTERS = [
    {"name": "رياض محرز ⚽🇩🇿", "traits": {"real": True, "male": True, "arabic": True, "footballer": True}},
    {"name": "كريستيانو رونالدو ⚽🇵🇹", "traits": {"real": True, "male": True, "arabic": False, "footballer": True}},
    {"name": "أبو فلّة 🎥", "traits": {"real": True, "male": True, "arabic": True, "footballer": False}},
    {"name": "سبونج بوب 🧽🟨", "traits": {"real": False, "male": True, "arabic": False, "footballer": False}}
]

QUESTIONS = [
    {"id": "real", "text": "❓ السؤال 1: هل الشخصية حقيقية؟ (ليست كرتونية)"},
    {"id": "male", "text": "❓ السؤال 2: هل الشخصية ذكر؟"},
    {"id": "arabic", "text": "❓ السؤال 3: هل الشخصية عربية؟"},
    {"id": "footballer", "text": "❓ السؤال 4: هل الشخصية لاعب كرة قدم؟"}
]

user_sessions = {}

@app.route("/", methods=["GET"])
def home():
    return "Bot is Running Successfully!", 200

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

def send_question_with_buttons(recipient_id, question_text):
    if not PAGE_ACCESS_TOKEN:
        return
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": question_text,
            "quick_replies": [
                {"content_type": "text", "title": "نعم ✅", "payload": "YES"},
                {"content_type": "text", "title": "لا ❌", "payload": "NO"},
                {"content_type": "text", "title": "لا أعلم 🤷‍♂️", "payload": "SKIP"}
            ]
        }
    }
    requests.post(url, json=payload)

def send_text(recipient_id, text):
    if not PAGE_ACCESS_TOKEN:
        return
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload)

def guess_character(answers):
    best_match = CHARACTERS[0]
    best_score = -100

    for char in CHARACTERS:
        score = 0
        for q_id, user_ans in answers.items():
            if user_ans is not None:
                if char["traits"].get(q_id) == user_ans:
                    score += 2
                else:
                    score -= 2
        if score > best_score:
            best_score = score
            best_match = char

    return best_match

@app.route("/webhook", methods=["POST"])
def webhook_post():
    data = request.get_json()

    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")

                if messaging.get("message"):
                    msg = messaging["message"]
                    user_text = msg.get("text", "").strip()

                    # التعامل مع الأزرار
                    if "quick_reply" in msg:
                        payload = msg["quick_reply"].get("payload")
                        if payload == "YES":
                            user_text = "نعم"
                        elif payload == "NO":
                            user_text = "لا"
                        elif payload == "SKIP":
                            user_text = "لا أعلم"

                    # إذا كان المستخدم في منتصف الجلسة ويجيب على الأسئلة
                    if sender_id in user_sessions and user_text in ["نعم", "لا", "لا أعلم"]:
                        session = user_sessions[sender_id]
                        step = session["step"]
                        q_id = QUESTIONS[step]["id"]

                        if user_text == "نعم":
                            session["answers"][q_id] = True
                        elif user_text == "لا":
                            session["answers"][q_id] = False
                        else:
                            session["answers"][q_id] = None

                        step += 1
                        session["step"] = step

                        if step < len(QUESTIONS):
                            send_question_with_buttons(sender_id, QUESTIONS[step]["text"])
                        else:
                            result = guess_character(session["answers"])
                            send_text(sender_id, f"🔮 المارد السحري يقول:\n\nالشخصية التي تفكر فيها هي:\n✨ {result['name']} ✨\n\nأرسل أي رسالة للعب مرة أخرى! 🧞‍♂️")
                            del user_sessions[sender_id]
                    else:
                        # لبدء اللعبة تلقائياً مع أي كلمة يرسلها المستخدم
                        user_sessions[sender_id] = {"step": 0, "answers": {}}
                        send_text(sender_id, "🧞‍♂️ أهلاً بك في لعبة المارد السحري!\nفكر في شخصية وسأقوم بتخمينها الآن عبر الأسئلة التالية 👇")
                        send_question_with_buttons(sender_id, QUESTIONS[0]["text"])

        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
