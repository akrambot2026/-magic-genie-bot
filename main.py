import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "akram12345"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

# رابط صورة المارد السحري
GENIE_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Akinator.png/600px-Akinator.png"

# قاعدة بيانات الأسئلة
QUESTIONS = [
    "هل الشخصية حقيقية؟",
    "هل الشخصية ذكر؟",
    "هل الشخصية عربية؟",
    "هل الشخصية يوتيوبر أو صانع محتوى؟",
    "هل الشخصية لاعب كرة قدم؟"
]

# ذاكرة بسيطة لحفظ حالة المستخدمين (رقم السؤال الحالي لكل مستخدم)
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
    """إرسال صورة المارد"""
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
    """إرسال السؤال مع أزرار تفاعلية (Quick Replies)"""
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
    """إرسال رسالة نصية عادية"""
    if not PAGE_ACCESS_TOKEN:
        return
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload)

@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()
    if body and body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                
                if messaging.get("message"):
                    user_text = messaging["message"].get("text", "").strip()
                    
                    # إذا كانت البداية أو طلب جديد
                    if user_text.lower() in ["بدء", "ابدأ", "مرحبا", "سلام", "start"]:
                        user_sessions[sender_id] = 0
                        send_image(sender_id, GENIE_IMAGE_URL)
                        send_text(sender_id, "أهلاً بك! أنا المارد السحري 🧞‍♂️\nفكر في شخصية وسأحاول تخمينها!")
                        send_question_with_buttons(sender_id, f"السؤال 1: {QUESTIONS[0]}")
                    
                    elif sender_id in user_sessions:
                        current_q = user_sessions[sender_id]
                        current_q += 1
                        
                        if current_q < len(QUESTIONS):
                            user_sessions[sender_id] = current_q
                            send_question_with_buttons(sender_id, f"السؤال {current_q + 1}: {QUESTIONS[current_q]}")
                        else:
                            # نهاية الأسئلة والتخمين
                            send_image(sender_id, GENIE_IMAGE_URL)
                            send_text(sender_id, "ممتاز! المارد السحري يفكر... 🤔💭\n\nالشخصية التي تفكر فيها هي: **رياض محرز** ⚽🔥\n\nأرسل 'ابدأ' للعب مرة أخرى!")
                            del user_sessions[sender_id]
                    else:
                        send_text(sender_id, "أهلاً بك! أرسل كلمة 'ابدأ' للعب مع المارد السحري! 🧞‍♂️")
                        
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
