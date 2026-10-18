import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "akram12345"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

# صور المارد والشخصيات
GENIE_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Akinator.png/600px-Akinator.png"

# قاعدة بيانات الشخصيات مع الصور والخصائص
CHARACTERS = [
    {
        "name": "رياض محرز",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Riyad_Mahrez_2018.jpg/440px-Riyad_Mahrez_2018.jpg",
        "traits": {"real": True, "male": True, "arabic": True, "footballer": True}
    },
    {
        "name": "أبو فلّة (AboFlah)",
        "image": "https://pbs.twimg.com/profile_images/1500000000000000000/example.jpg", # رابط صورة أبو فلة
        "traits": {"real": True, "male": True, "arabic": True, "footballer": False, "youtuber": True}
    },
    {
        "name": "سبونج بوب",
        "image": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/SpongeBob_SquarePants_character.svg/400px-SpongeBob_SquarePants_character.svg.png",
        "traits": {"real": False, "male": True}
    }
]

# قائمة الأسئلة مرتبة
QUESTIONS = [
    {"id": "real", "text": "هل الشخصية حقيقية؟"},
    {"id": "male", "text": "هل الشخصية ذكر؟"},
    {"id": "arabic", "text": "هل الشخصية عربية؟"},
    {"id": "footballer", "text": "هل الشخصية لاعب كرة قدم؟"},
    {"id": "youtuber", "text": "هل الشخصية يوتيوبر أو صانع محتوى؟"}
]

# حفظ بيانات الجلسات لكل مستخدم
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

def guess_character(answers):
    """دالة الذكاء لاختيار أفضل شخصية بناءً على إجابات المستخدم"""
    for char in CHARACTERS:
        match = True
        for trait, val in char["traits"].items():
            if trait in answers and answers[trait] != val:
                match = False
                break
        if match:
            return char
    return CHARACTERS[0]  # افتراضي

@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()
    if body and body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                
                if messaging.get("message"):
                    user_text = messaging["message"].get("text", "").strip()
                    
                    # بدء لعبة جديدة
                    if user_text.lower() in ["بدء", "ابدأ", "مرحبا", "سلام", "start"]:
                        user_sessions[sender_id] = {
                            "step": 0,
                            "answers": {}
                        }
                        send_image(sender_id, GENIE_IMAGE)
                        send_text(sender_id, "أهلاً بك! أنا المارد السحري 🧞‍♂️\nفكر في شخصية في عقلك وسأقوم بتخمينها!")
                        send_question_with_buttons(sender_id, f"السؤال 1: {QUESTIONS[0]['text']}")
                    
                    elif sender_id in user_sessions:
                        session = user_sessions[sender_id]
                        step = session["step"]
                        q_id = QUESTIONS[step]["id"]
                        
                        # حفظ الإجابة
                        if "نعم" in user_text:
                            session["answers"][q_id] = True
                        elif "لا" in user_text:
                            session["answers"][q_id] = False
                            
                        step += 1
                        session["step"] = step
                        
                        if step < len(QUESTIONS):
                            send_question_with_buttons(sender_id, f"السؤال {step + 1}: {QUESTIONS[step]['text']}")
                        else:
                            # مرحلة التخمين النهائية
                            result = guess_character(session["answers"])
                            send_text(sender_id, f"لقد قرأت أفكارك! 🔮\n\nالشخصية التي تفكر فيها هي:\n🌟 **{result['name']}** 🌟")
                            send_image(sender_id, result["image"])
                            send_text(sender_id, "أرسل 'ابدأ' لتحدي المارد مرة أخرى! 🧞‍♂️")
                            del user_sessions[sender_id]
                    else:
                        send_text(sender_id, "أهلاً بك! أرسل كلمة 'ابدأ' للعب مع المارد السحري! 🧞‍♂️")
                        
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
