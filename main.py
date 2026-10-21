import os
import json
import time
import logging
import sqlite3
import unicodedata
import requests

from flask import Flask, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("GeniePro")

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "CHANGE_THIS_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GRAPH_VERSION = os.environ.get("GRAPH_API_VERSION", "v23.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}/me/messages"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/tmp/genie_sessions.db")

HTTP = requests.Session()

# ==========================================
# 🧞‍♂️ أسئلة المارد الأزرق
# ==========================================

QUESTIONS = [
    "هل الشخصية حقيقية؟ 🤔",
    "هل الشخصية ذكر؟ 👤",
    "هل الشخصية عربية؟ 🌍",
    "هل الشخصية لاعب كرة قدم؟ ⚽",
    "هل الشخصية من الأنمي؟ 🍥",
    "هل الشخصية خيالية؟ ✨",
    "هل اشتهرت في الرياضة؟ 🏆",
    "هل هي مغنٍ أو فنان موسيقي؟ 🎤",
    "هل هي صانع محتوى؟ 🎥",
    "هل هي بطل خارق؟ 🦸",
    "هل تظهر في ناروتو أو بوروتو؟ 🍃",
    "هل تظهر في دراغون بول؟ 🐉"
]


def traits(real, male, arab, football, anime,
           fiction, sports, singer, youtube,
           superhero, naruto, dragonball):
    return [
        real, male, arab, football, anime,
        fiction, sports, singer, youtube,
        superhero, naruto, dragonball
    ]


# ==========================================
# 🌍 قاعدة الشخصيات
# ترتيب الصفات مطابق لترتيب الأسئلة
# ==========================================

CHARACTERS = [
    {
        "name": "رياض محرز",
        "emoji": "⚽🇩🇿",
        "wiki": "Riyad_Mahrez",
        "traits": traits(True, True, True, True, False,
                         False, True, False, False, False, False, False)
    },
    {
        "name": "كريستيانو رونالدو",
        "emoji": "⚽🇵🇹",
        "wiki": "Cristiano_Ronaldo",
        "traits": traits(True, True, False, True, False,
                         False, True, False, False, False, False, False)
    },
    {
        "name": "ليونيل ميسي",
        "emoji": "⚽🇦🇷",
        "wiki": "Lionel_Messi",
        "traits": traits(True, True, False, True, False,
                         False, True, False, False, False, False, False)
    },
    {
        "name": "كيليان مبابي",
        "emoji": "⚽🇫🇷",
        "wiki": "Kylian_Mbappe",
        "traits": traits(True, True, False, True, False,
                         False, True, False, False, False, False, False)
    },
    {
        "name": "محمد صلاح",
        "emoji": "⚽🇪🇬",
        "wiki": "Mohamed_Salah",
        "traits": traits(True, True, True, True, False,
                         False, True, False, False, False, False, False)
    },
    {
        "name": "أشرف حكيمي",
        "emoji": "⚽🇲🇦",
        "wiki": "Achraf_Hakimi",
        "traits": traits(True, True, True, True, False,
                         False, True, False, False, False, False, False)
    },
    {
        "name": "أبو فلة",
        "emoji": "🎥",
        "wiki": "Aboflah",
        "traits": traits(True, True, True, False, False,
                         False, False, False, True, False, False, False)
    },
    {
        "name": "مستر بيست",
        "emoji": "🎁",
        "wiki": "MrBeast",
        "traits": traits(True, True, False, False, False,
                         False, False, False, True, False, False, False)
    },
    {
        "name": "ناروتو أوزوماكي",
        "emoji": "🍥",
        "wiki": "Naruto_Uzumaki",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "ساسكي أوتشيها",
        "emoji": "⚡",
        "wiki": "Sasuke_Uchiha",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "إيتاتشي أوتشيها",
        "emoji": "🐦‍⬛",
        "wiki": "Itachi_Uchiha",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "أوبيتو أوتشيها",
        "emoji": "🌀",
        "wiki": "Obito_Uchiha",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "كاكاشي هاتاكي",
        "emoji": "⚡",
        "wiki": "Kakashi_Hatake",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "مادارا أوتشيها",
        "emoji": "🔥",
        "wiki": "Madara_Uchiha",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "بوروتو أوزوماكي",
        "emoji": "🌪️",
        "wiki": "Boruto_Uzumaki",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, True, False)
    },
    {
        "name": "غوكو",
        "emoji": "🐉",
        "wiki": "Goku",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, False, True)
    },
    {
        "name": "فيجيتا",
        "emoji": "💥",
        "wiki": "Vegeta",
        "traits": traits(False, True, False, False, True,
                         True, False, False, False, False, False, True)
    },
    {
        "name": "سبونج بوب",
        "emoji": "🧽",
        "wiki": "SpongeBob_SquarePants",
        "traits": traits(False, False, False, False, False,
                         True, False, False, False, False, False, False)
    },
    {
        "name": "باربي",
        "emoji": "👱‍♀️",
        "wiki": "Barbie",
        "traits": traits(False, False, False, False, False,
                         True, False, False, False, False, False, False)
    },
    {
        "name": "باتمان",
        "emoji": "🦇",
        "wiki": "Batman",
        "traits": traits(False, True, False, False, False,
                         True, False, False, False, True, False, False)
    },
    {
        "name": "سوبرمان",
        "emoji": "🦸",
        "wiki": "Superman",
        "traits": traits(False, True, False, False, False,
                         True, False, False, False, True, False, False)
    },
    {
        "name": "سبايدرمان",
        "emoji": "🕷️",
        "wiki": "Spider-Man",
        "traits": traits(False, True, False, False, False,
                         True, False, False, False, True, False,
