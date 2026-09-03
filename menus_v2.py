from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from i18n import LANGUAGES, t


def language_keyboard():
    items = list(LANGUAGES.items())
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(items[i][1], callback_data=f"lang:{items[i][0]}"), InlineKeyboardButton(items[i+1][1], callback_data=f"lang:{items[i+1][0]}")]
        for i in range(0, len(items), 2)
    ])


def main_menu(lang: str = "uz"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "create"), callback_data="create_menu")],
        [InlineKeyboardButton(t(lang, "join"), callback_data="join_general")],
        [InlineKeyboardButton(t(lang, "single"), callback_data="join_single")],
        [InlineKeyboardButton(t(lang, "mine"), callback_data="my_tests")],
        [InlineKeyboardButton(t(lang, "language"), callback_data="choose_language")],
        [InlineKeyboardButton(t(lang, "help"), callback_data="help")],
    ])


def create_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Faqat umumiy quiz", callback_data="new:quiz")],
        [InlineKeyboardButton("✍️ Faqat umumiy yozma", callback_data="new:written")],
        [InlineKeyboardButton("🧠 + ✍️ Quiz va yozma", callback_data="new:combined")],
        [InlineKeyboardButton("👤 Yakka test", callback_data="new:single")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back:main")],
    ])


def session_actions(session_id: int, state: str):
    rows = []
    if state in {"draft", "scheduled"}:
        rows.append([InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit:{session_id}"), InlineKeyboardButton("🚫 Bekor qilish", callback_data=f"cancel:{session_id}")])
    if state == "finished":
        rows.append([InlineKeyboardButton("🔁 Qayta ishga tushirish", callback_data=f"rerun:{session_id}"), InlineKeyboardButton("📊 Natijalar", callback_data=f"results:{session_id}")])
    rows.append([InlineKeyboardButton("🗑 Butunlay o‘chirish", callback_data=f"delete:{session_id}")])
    return InlineKeyboardMarkup(rows)
