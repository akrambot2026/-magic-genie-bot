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
    return "Akinator Bot Status: Online & Ready!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello world", 200

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

def smart_guess(answers):
    best_match = CHARACTERS[0]
    highest_score = -10

    for char in CHARACTERS:
        score = 0
        is_possible = True
        
        for q_id, user_ans in answers.items():
            if user_ans is None:
                continue
            
            char_trait = char["traits"].get(q_id)
            if char_trait is not None:
                if char_trait == user_ans:
                    score += 3
                else:
                    score -= 5
                    is_possible = False
        
        if is_possible and score > highest_score:
            highest_score = score
            best_match = char

    return best_match

@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()
    if body and body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                
                if messaging.get("message"):
                    user_text = messaging["message"].get("text", "").strip()
                    
                    if "بدء" in user_text.lower() or "start" in user_text.lower():
                        user_sessions[sender_id] = {
                            "step": 0,
                            "answers": {}
                        }
                        send_image(sender_id, GENIE_IMAGE)
                        send_text(sender_id, "أهلاً بك! أنا المارد السحري 🧞‍♂️🔮\nفكر في شخصية وسأقوم بتخمينها الآن!")
                        send_question_with_buttons(sender_id, f"السؤال 1: {QUESTIONS[0]['text']}")
                    
                    elif sender_id in user_sessions:
                        session = user_sessions[sender_id]
                        step = session["step"]
                        q_id = QUESTIONS[step]["id"]
                        
                        if "نعم" in user_text:
                            session["answers"][q_id] = True
                        elif "لا" in user_text:
                            session["answers"][q_id] = False
                        else:
                            session["answers"][q_id] = None
                            
                        step += 1
                        session["step"] = step
                        
                        if step < len(QUESTIONS):
                            send_question_with_buttons(sender_id, f"السؤال {step + 1}: {QUESTIONS[step]['text']}")
                        else:
                            result = smart_guess(session["answers"])
                            send_text(sender_id, f"لقد قمت بتحليل أفكارك بنجاح! 🔮🧠\n\nالشخصية هي:\n✨ **{result['name']}** ✨")
                            send_image(sender_id, result["image"])
                            send_text(sender_id, "أرسل 'ابدأ' لتحدي المارد من جديد! 🧞‍♂️")
                            del user_sessions[sender_id]
                    else:
                        send_text(sender_id, "أهلاً بك! أرسل كلمة 'ابدأ' لبدء اللعب مع المارد السحري! 🧞‍♂️")
                        
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
