import os
import logging
import requests

from flask import Flask, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# =========================
# إعدادات البوت
# =========================

VERIFY_TOKEN = os.environ.get(
    "VERIFY_TOKEN",
    "akram12345"
)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

GRAPH_API_URL = "https://graph.facebook.com/v23.0/me/messages"

# =========================
# الشخصيات
# =========================

CHARACTERS = [
    {
        "name": "رياض محرز ⚽🇩🇿",
        "traits": {
            "real": True,
            "male": True,
            "arabic": True,
            "footballer": True,
            "famous": True
        }
    },
    {
        "name": "كريستيانو رونالدو ⚽🇵🇹",
        "traits": {
            "real": True,
            "male": True,
            "arabic": False,
            "footballer": True,
            "famous": True
        }
    },
    {
        "name": "ليونيل ميسي ⚽🇦🇷",
        "traits": {
            "real": True,
            "male": True,
            "arabic": False,
            "footballer": True,
            "famous": True
        }
    },
    {
        "name": "أبو فلّة 🎥",
        "traits": {
            "real": True,
            "male": True,
            "arabic": True,
            "footballer": False,
            "famous": True
        }
    },
    {
        "name": "سبونج بوب 🧽",
        "traits": {
            "real": False,
            "male": True,
            "arabic": False,
            "footballer": False,
            "famous": True
        }
    },
    {
        "name": "باتمان 🦇",
        "traits": {
            "real": False,
            "male": True,
            "arabic": False,
            "footballer": False,
            "famous": True
        }
    },
    {
        "name": "باربي 👱‍♀️",
        "traits": {
            "real": False,
            "male": False,
            "arabic": False,
            "footballer": False,
            "famous": True
        }
    },
    {
        "name": "أمك ❤️",
        "traits": {
            "real": True,
            "male": False,
            "arabic": True,
            "footballer": False,
            "famous": False
        }
    }
]

# =========================
# الأسئلة
# =========================

QUESTIONS = [
    {
        "id": "real",
        "text": "هل الشخصية حقيقية؟ 🤔"
    },
    {
        "id": "male",
        "text": "هل الشخصية ذكر؟ 👤"
    },
    {
        "id": "arabic",
        "text": "هل الشخصية عربية؟ 🌍"
    },
    {
        "id": "footballer",
        "text": "هل الشخصية لاعب كرة قدم؟ ⚽"
    },
    {
        "id": "famous",
        "text": "هل الشخصية مشهورة؟ ⭐"
    }
]

# تخزين الجلسات في ذاكرة البرنامج
user_sessions = {}


# =========================
# إرسال الرسائل
# =========================

def send_message(recipient_id, message):
    if not PAGE_ACCESS_TOKEN:
        app.logger.error("PAGE_ACCESS_TOKEN غير مضبوط")
        return False

    payload = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": message
    }

    try:
        response = requests.post(
            GRAPH_API_URL,
            params={"access_token": PAGE_ACCESS_TOKEN},
            json=payload,
            timeout=15
        )

        if not response.ok:
            app.logger.error(
                "Facebook API error: %s",
                response.text
            )
            return False

        app.logger.info("Message sent successfully")
        return True

    except requests.RequestException:
        app.logger.exception("Message sending failed")
        return False


def send_text(recipient_id, text):
    return send_message(
        recipient_id,
        {"text": text}
    )


def send_question(recipient_id, question):
    return send_message(
        recipient_id,
        {
            "text": question,
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "نعم ✅",
                    "payload": "ANSWER_YES"
                },
                {
                    "content_type": "text",
                    "title": "لا ❌",
                    "payload": "ANSWER_NO"
                },
                {
                    "content_type": "text",
                    "title": "لا أعلم 🤷",
                    "payload": "ANSWER_SKIP"
                }
            ]
        }
    )


# =========================
# تخمين الشخصية
# =========================

def guess_character(answers):
    best_character = None
    best_score = -999

    for character in CHARACTERS:
        score = 0

        for question_id, answer in answers.items():
            if answer is None:
                continue

            expected = character["traits"].get(question_id)

            if expected == answer:
                score += 2
            else:
                score -= 2

        if score > best_score:
            best_score = score
            best_character = character

    return best_character


# =========================
# بدء اللعبة
# =========================

def start_game(sender_id):
    user_sessions[sender_id] = {
        "step": 0,
        "answers": {}
    }

    send_text(
        sender_id,
        "🔥 أهلاً بك في المارد السحري 🔥\n\n"
        "فكّر في شخصية مشهورة، وسأحاول تخمينها!\n"
        "أجب عن الأسئلة باستخدام الأزرار 👇"
    )

    send_question(
        sender_id,
        QUESTIONS[0]["text"]
    )


# =========================
# معالجة الإجابة
# =========================

def process_answer(sender_id, answer):
    session = user_sessions.get(sender_id)

    if session is None:
        start_game(sender_id)
        return

    step = session["step"]

    if step >= len(QUESTIONS):
        start_game(sender_id)
        return

    question_id = QUESTIONS[step]["id"]

    session["answers"][question_id] = answer
    session["step"] += 1

    next_step = session["step"]

    if next_step < len(QUESTIONS):
        send_question(
            sender_id,
            QUESTIONS[next_step]["text"]
        )
        return

    result = guess_character(session["answers"])

    if result is None:
        send_text(
            sender_id,
            "لم أتمكن من تخمين الشخصية 😅"
        )
    else:
        send_text(
            sender_id,
            "🔮 المارد السحري يتوقع...\n\n"
            f"✨ شخصيتك هي: {result['name']} ✨\n\n"
            "هل أصبت التخمين؟ 😎\n"
            "أرسل «ابدأ» للعب مرة أخرى."
        )

    user_sessions.pop(sender_id, None)


# =========================
# الصفحة الرئيسية
# =========================

@app.route("/", methods=["GET"])
def home():
    return "🔥 Genie Bot is Running!", 200


# =========================
# التحقق من Webhook
# =========================

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge or "", 200

    return "Verification failed", 403


# =========================
# استقبال رسائل Messenger
# =========================

@app.route("/webhook", methods=["POST"])
def webhook_post():
    data = request.get_json(silent=True)

    if not data or data.get("object") != "page":
        return "Not Found", 404

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):

            # تجاهل أحداث التسليم والقراءة
            if event.get("delivery") or event.get("read"):
                continue

            sender_id = event.get("sender", {}).get("id")

            if not sender_id:
                continue

            # تجاهل الرسائل التي يرسلها صاحب الصفحة
            if event.get("message", {}).get("is_echo"):
                continue

            message = event.get("message", {})

            if not message:
                continue

            # استخراج الإجابة من الزر أو النص
            quick_reply = message.get("quick_reply", {})
            payload = quick_reply.get("payload", "")

            text = (
                message.get("text") or ""
            ).strip().lower()

            if payload == "ANSWER_YES":
                answer = True

            elif payload == "ANSWER_NO":
                answer = False

            elif payload == "ANSWER_SKIP":
                answer = None

            elif text in ["نعم", "اي", "أجل", "yes", "y"]:
                answer = True

            elif text in ["لا", "no", "n"]:
                answer = False

            elif text in [
                "لا أعلم",
                "لا اعلم",
                "ربما",
                "تخطي",
                "skip"
            ]:
                answer = None

            else:
                # بدء لعبة جديدة عند عدم وجود جلسة
                if (
                    sender_id not in user_sessions
                    or text in [
                        "ابدأ",
                        "ابدا",
                        "ابدأ اللعبة",
                        "العب",
                        "start",
                        "restart"
                    ]
                ):
                    start_game(sender_id)

                else:
                    send_text(
                        sender_id,
                        "👇 اختر إجابتك من الأزرار "
                        "الموجودة تحت السؤال.\n\n"
                        "نعم ✅ أو لا ❌ أو لا أعلم 🤷"
                    )

                continue

            process_answer(sender_id, answer)

    return "EVENT_RECEIVED", 200


# =========================
# تشغيل السيرفر
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
