import os
import logging
import requests

from flask import Flask, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "12345")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

GRAPH_URL = "https://graph.facebook.com/v18.0/me/messages"

# الشخصيات التي يستطيع البوت تخمينها
CHARACTERS = [
    {
        "name": "رياض محرز ⚽🇩🇿",
        "traits": [True, True, True, True]
    },
    {
        "name": "كريستيانو رونالدو ⚽🇵🇹",
        "traits": [True, True, False, True]
    },
    {
        "name": "ليونيل ميسي ⚽🇦🇷",
        "traits": [True, True, False, True]
    },
    {
        "name": "أبو فلّة 🎥",
        "traits": [True, True, True, False]
    },
    {
        "name": "سبونج بوب 🧽",
        "traits": [False, True, False, False]
    },
    {
        "name": "باربي 👱‍♀️",
        "traits": [False, False, False, False]
    },
    {
        "name": "باتمان 🦇",
        "traits": [False, True, False, False]
    }
]

QUESTIONS = [
    "هل الشخصية حقيقية؟ 🤔",
    "هل الشخصية ذكر؟ 👤",
    "هل الشخصية عربية؟ 🌍",
    "هل الشخصية لاعب كرة قدم؟ ⚽"
]

# جلسات اللاعبين
sessions = {}


def send_message(user_id, message):
    """إرسال رسالة مع تسجيل أخطاء Facebook."""
    if not PAGE_ACCESS_TOKEN:
        app.logger.error("PAGE_ACCESS_TOKEN غير موجود في Environment")
        return False

    try:
        response = requests.post(
            GRAPH_URL,
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": user_id},
                "messaging_type": "RESPONSE",
                "message": message
            },
            timeout=15
        )

        if not response.ok:
            app.logger.error(
                "Facebook API HTTP %s: %s",
                response.status_code,
                response.text
            )
            return False

        app.logger.info("تم إرسال الرسالة إلى Messenger")
        return True

    except requests.RequestException:
        app.logger.exception("تعذر الاتصال بـ Facebook")
        return False


def send_text(user_id, text):
    return send_message(user_id, {"text": text})


def send_question(user_id, index):
    return send_message(
        user_id,
        {
            "text": QUESTIONS[index],
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "نعم ✅",
                    "payload": "YES"
                },
                {
                    "content_type": "text",
                    "title": "لا ❌",
                    "payload": "NO"
                },
                {
                    "content_type": "text",
                    "title": "لا أعلم 🤷",
                    "payload": "SKIP"
                }
            ]
        }
    )


def start_game(user_id):
    sessions[user_id] = {
        "step": 0,
        "answers": []
    }

    send_text(
        user_id,
        "🔥 أهلاً بك في المارد السحري!\n\n"
        "فكّر في شخصية، وأجب عن الأسئلة لأحاول تخمينها.\n"
        "لنبدأ! 🧞"
    )

    send_question(user_id, 0)


def guess_character(answers):
    best_character = None
    best_score = -1

    for character in CHARACTERS:
        score = 0

        for index, answer in enumerate(answers):
            if answer is None:
                continue

            if character["traits"][index] == answer:
                score += 1

        if score > best_score:
            best_score = score
            best_character = character

    return best_character


def handle_answer(user_id, answer):
    session = sessions.get(user_id)

    if session is None:
        start_game(user_id)
        return

    step = session["step"]

    if step >= len(QUESTIONS):
        start_game(user_id)
        return

    session["answers"].append(answer)
    session["step"] += 1

    next_step = session["step"]

    if next_step < len(QUESTIONS):
        send_question(user_id, next_step)
        return

    result = guess_character(session["answers"])

    send_text(
        user_id,
        "🔮 انتهى المارد من التفكير!\n\n"
        f"✨ أتوقع أن شخصيتك هي: {result['name']} ✨\n\n"
        "للعب مجدداً، أرسل: ابدأ"
    )

    sessions.pop(user_id, None)


@app.route("/", methods=["GET"])
def home():
    return "Genie Bot is running!", 200


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge or "", 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return "EVENT_RECEIVED", 200

    if data.get("object") != "page":
        return "Not a page event", 404

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):

            # تجاهل أحداث التسليم والقراءة
            if "delivery" in event or "read" in event:
                continue

            sender = event.get("sender", {}).get("id")

            if not sender:
                continue

            message = event.get("message", {})

            # تجاهل رسائل الصفحة نفسها
            if message.get("is_echo"):
                continue

            if not message:
                continue

            app.logger.info("وصل حدث رسالة من Messenger")

            # قراءة ضغط الأزرار
            quick_reply = message.get("quick_reply", {})
            payload = quick_reply.get("payload", "")

            text = (message.get("text") or "").strip().lower()

            if payload == "YES":
                answer = True

            elif payload == "NO":
                answer = False

            elif payload == "SKIP":
                answer = None

            elif text in ("نعم", "اي", "أجل", "yes", "y"):
                answer = True

            elif text in ("لا", "no", "n"):
                answer = False

            elif text in ("لا أعلم", "لا اعلم", "تخطي", "skip", "ربما"):
                answer = None

            elif text in ("ابدأ", "ابدا", "ابدأ اللعبة", "العب", "start", "restart", "مرحبا", "سلام"):
                start_game(sender)
                continue

            else:
                if sender not in sessions:
                    start_game(sender)
                else:
                    send_text(
                        sender,
                        "من فضلك أجب باستخدام الأزرار: نعم أو لا أو لا أعلم."
                    )
                continue

            handle_answer(sender, answer)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
