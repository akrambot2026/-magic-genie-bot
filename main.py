@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()
    if body and body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                
                if messaging.get("message"):
                    message_obj = messaging["message"]
                    user_text = message_obj.get("text", "").strip()
                    
                    # التحقق إذا كان المستخدم ضغط على زر السريع أو كتب نصاً
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
                        
                        # تحليل إجابة المستخدم بدقة
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
