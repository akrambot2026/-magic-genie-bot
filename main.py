import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "akram12345"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

# صورة المارد السحري الرئيسية (رابط مباشر موثوق)
GENIE_IMAGE = "https://i.ibb.co/L8vT9J3/akinator.png"

# قاعدة بيانات الشخصيات مع روابط صور مباشرة وحقيقية
CHARACTERS = [
    {
        "name": "رياض محرز ⚽🇩🇿",
        "image": "https://i.ibb.co/3kXf58q/mahrez.jpg",
        "traits": {"real": True, "male": True, "arabic": True, "footballer": True, "youtuber": False}
    },
    {
        "name": "كريستيانو رونالدو ⚽🇵🇹",
        "image": "https://i.ibb.co/BszMvQq/ronaldo.jpg",
        "traits": {"real": True, "male": True, "arabic": False, "footballer": True, "youtuber": False}
    },
    {
        "name": "أبو فلّة (AboFlah) 🎥",
        "image": "https://i.ibb.co/mSRwzbd/aboflah.jpg",
        "traits": {"real": True, "male": True, "arabic": True, "footballer": False, "youtuber": True}
    },
    {
        "name": "سبونج بوب 🧽🟨",
        "image": "https://i.ibb.co/S3J0Yw2/spongebob.png",
        "traits": {"real": False, "male": True, "arabic": False, "footballer": False, "youtuber": False}
    },
    {
        "name": "ليونيل ميسي ⚽🇦🇷",
        "image": "https://i.ibb.co/YPXK6jH/messi.jpg",
        "traits": {"real": True, "male": True, "arabic": False, "footballer": True, "youtuber": False}
    }
]

# قائمة الأسئلة
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
    return "Akinator Bot is running successfully!", 200

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
    """إرسال صور موثوقة إلى فيسبوك"""
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
    res = requests.post(url, json=payload)
    print("Image Sent Result:", res.text)

def send_question_with_buttons(recipient_id, question_text):
    """إرسال 6 أزرار تفاعلية شبيها بـ Akinator الأصلي"""
    if not PAGE_ACCESS_TOKEN:
        return
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": question_text,
            "quick_replies": [
                {"content_type": "text", "title": "نعم ✅", "payload": "YES"},
                {"content_type": "text", "title": "غالباً نعم 👍", "payload": "MOSTLY_YES"},
                {"content_type": "text", "title": "لا أعلم 🤷‍♂️", "payload": "DONT_KNOW"},
                {"content_type": "text", "title": "غالباً لا 👎", "payload": "MOSTLY_NO"},
                {"content_type": "text", "title": "لا ❌", "payload": "NO"}
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
    """محرك التخمين الذكي بأسلوب حساب النقاط والمطابقة الدقيقة"""
    best_char = None
    max_score = -999

    for char in CHARACTERS:
        score = 0
        possible = True
        
        for trait_id, user_val in answers.items():
            if user_val is None:
                continue
            char_val = char["traits"].get(trait_id)
            if char_val is not None:
                if char_val == user_val:
                    score += 2
                else:
                    # تخصيم نقاط واستبعاد إذا كان التناقض صريحاً
                    score -= 5
                    possible = False
        
        if score > max_score:
            max_score = score
            best_char = char
            
    return best_char if best_char else CHARACTERS[0]

@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()
    if body and body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                
                if messaging.get("message"):
                    user_text = messaging["message"].get("text", "").strip()
                    
                    # بدء اللعبة
                    if user_text.lower() in ["بدء", "ابدأ", "مرحبا", "سلام", "start"]:
                        user_sessions[sender_id] = {
                            "step": 0,
                            "answers": {}
                        }
                        send_image(sender_id, GENIE_IMAGE)
                        send_text(sender_id, "أهلاً بك! أنا المارد السحري الذكي 🧞‍♂️🔮\nفكر في شخصية وسأقرأ أفكارك الآن!")
                        send_question_with_buttons(sender_id, f"السؤال 1: {QUESTIONS[0]['text']}")
                    
                    elif sender_id in user_sessions:
                        session = user_sessions[sender_id]
                        step = session["step"]
                        q_id = QUESTIONS[step]["id"]
                        
                        # تحليل رد المستخدم وتحويله إلى قيمة منطقية
                        if "نعم" in user_text:
                            session["answers"][q_id] = True
                        elif "لا" in user_text and "أعلم" not in user_text:
                            session["answers"][q_id] = False
                        else:
                            session["answers"][q_id] = None # لا أعلم أو محايد
                            
                        step += 1
                        session["step"] = step
                        
                        if step < len(QUESTIONS):
                            send_question_with_buttons(sender_id, f"السؤال {step + 1}: {QUESTIONS[step]['text']}")
                        else:
                            # حساب الشخصية وترشيح الصورة والنتيجة
                            result = smart_guess(session["answers"])
                            send_text(sender_id, f"لقد حللت أفكارك بنجاح! 🔮🧠\n\nالشخصية التي تفكر فيها هي:\n✨ **{result['name']}** ✨")
                            send_image(sender_id, result["image"])
                            send_text(sender_id, "أرسل 'ابدأ' لتحدي المارد من جديد! 🧞‍♂️")
                            del user_sessions[sender_id]
                    else:
                        send_text(sender_id, "أهلاً بك! أرسل كلمة 'ابدأ' لبدء تحدي المارد السحري! 🧞‍♂️")
                        
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
