import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "akram12345"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

GENIE_IMAGE = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop"

CHARACTERS = [
    {
        "name": "رياض محرز ⚽🇩🇿",
        "image": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500&auto=format&fit=crop",
        "traits": {"real": True, "male": True, "arabic": True, "footballer": True, "youtuber": False}
    },
    {
        "name": "كريستيانو رونالدو ⚽🇵🇹",
        "image": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=500&auto=format&fit=crop",
        "traits": {"real": True, "male": True, "arabic": False, "footballer": True, "youtuber": False}
    },
    {
        "name": "أبو فلّة (AboFlah) 🎥",
        "image": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&auto=format&fit=crop",
        "traits": {"real": True, "male": True, "arabic": True, "footballer": False, "youtuber": True}
    },
    {
        "name": "سبونج بوب 🧽🟨",
        "image": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop",
        "traits": {"real": False, "male": True, "arabic": False, "footballer": False, "youtuber": False}
    }
]

QUESTIONS = [
    {"id": "real", "text": "هل الشخصية حقيقية؟ (ليست كرتونية)"},
    {"id": "male", "text": "هل الشخصية ذكر؟"},
    {"id": "arabic", "text": "هل الشخصية عربية أو من أصل عربي؟"},
    {"id": "footballer", "text": "هل الشخصية لاعب كرة قدم محترف؟"},
    {"id": "youtuber", "text": "هل الشخصية صانع محتوى أو يوتيوبر شهير؟"}
]

user_sessions = {}

@app.route("/", methods=["GET"])
def home():
    return "Akinator Bot Online", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token and mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

def send_image(recipient_id, image_url):
    if not PAGE_ACCESS_TOKEN:
        return
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url, "is_reusable": True}
            }
        }
    }
    requests.post(url, json=payload)

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
                {"content_type": "text", "title": "لا أعلم 🤷‍♂️", "payload": "DONT_KNOW"}
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

def get_best_guess(answers):
    best_match = CHARACTERS[0]
    max_score = -100

    for char in CHARACTERS:
        score = 0
        for q_id, user_ans in answers.items():
            if user_ans is not None:
                if char["traits"].get(q_id) == user_ans:
                    score += 2
                else:
                    score -= 3
        if score > max_score:
            max_score = score
            best_match = char

    return best_match

@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()
    
    if body and body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                
                user_text = ""
                if messaging.get("message"):
                    msg = messaging["message"]
                    user_text = msg.get("text", "").strip()
                    if "quick_reply" in msg:
                        payload_val = msg["quick_reply"].get("payload", "")
                        if payload_val == "YES":
                            user_text = "نعم"
                        elif payload_val == "NO":
                            user_text = "لا"
                        elif payload_val == "DONT_KNOW":
                            user_text = "لا أعلم"

                if user_text:
                    if "ابدأ" in user_text.lower() or "start" in user_text.lower():
                        user_sessions[sender_id] = {"step": 0, "answers": {}}
                        send_image(sender_id, GENIE_IMAGE)
                        send_text(sender_id, "أهلاً بك! أنا المارد السحري 🧞‍♂️🔮\nفكر في شخصية وسأحاول تخمينها!")
                        send_question_with_buttons(sender_id, f"السؤال 1: {QUESTIONS[0]['text']}")
                    
                    elif sender_id in user_sessions:
                        session =
