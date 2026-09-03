from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, Update, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from core_v2 import (
    connect, create_attempt, create_or_get_participant, create_session, current_attempt_question,
    decode, encode, finish_attempt, init_schema, iso_now, make_code,
)
from grading_v2 import check_written_answer
from i18n import LANGUAGES, t
from pdf_v2 import build_certificate, build_test_pdf

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("V2_DB_PATH", "bilimbellashuv_v2.sqlite3")
MINI_APP_URL = os.getenv("MINI_APP_URL", "").strip().rstrip("/")
DEFAULT_TZ = "Asia/Tashkent"
LETTERS = "ABCD"
LOG_PATH = Path(os.getenv("V2_LOG_PATH", "bilimbellashuv_errors.log"))
logging.basicConfig(filename=str(LOG_PATH), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bilimbellashuv")


def db(): return connect(DB_PATH)

def lang(context): return context.user_data.get("lang", "uz")

def main_menu(context):
    l = lang(context); rows = []
    if MINI_APP_URL.startswith("https://"):
        rows.append([InlineKeyboardButton("🧩 Oynada test yaratish", web_app=WebAppInfo(url=MINI_APP_URL))])
    rows += [[InlineKeyboardButton(t(l, "create"), callback_data="new_bank")],
             [InlineKeyboardButton(t(l, "join"), callback_data="join_general"), InlineKeyboardButton(t(l, "single"), callback_data="join_single")],
             [InlineKeyboardButton(t(l, "mine"), callback_data="my_tests")],
             [InlineKeyboardButton(t(l, "language"), callback_data="languages")],
             [InlineKeyboardButton(t(l, "help"), callback_data="help")]]
    return InlineKeyboardMarkup(rows)


def language_keyboard():
    items = list(LANGUAGES.items())
    return InlineKeyboardMarkup([[InlineKeyboardButton(items[i][1], callback_data=f"setlang:{items[i][0]}") for i in range(j, min(j + 2, len(items)))] for j in range(0, len(items), 2)])


def now_utc(): return datetime.now(timezone.utc)

def parse_utc(value):
    if not value: return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError: return None

def safe_int(value, default=0):
    try: return int(value)
    except (TypeError, ValueError): return default

def settings_for(session, phase): return decode(session["written_settings_json"] if phase == "written" else session["quiz_settings_json"], {})

def type_for_session(c, session):
    row = c.execute("SELECT test_type FROM quiz_banks WHERE id=?", (session["bank_id"],)).fetchone()
    return row["test_type"] if row else "quiz"


async def start(update, context):
    if not context.user_data.get("lang"):
        await update.effective_message.reply_text("Tilni tanlang / Выберите язык / Choose a language:", reply_markup=language_keyboard()); return
    await update.effective_message.reply_text("BilimBellashuv Bot\n\nG‘oya/Loyiha muallifi: Gulmira Norpulatova\nLoyihalashtiruvchi: AI\nKanal: https://t.me/FAKTastika1\n\nKerakli bo‘limni tanlang.", reply_markup=main_menu(context))


async def language_list(update, context):
    q = update.callback_query; await q.answer(); await q.edit_message_text(t(lang(context), "choose_language"), reply_markup=language_keyboard())


async def set_language(update, context):
    q = update.callback_query; await q.answer(); context.user_data["lang"] = q.data.split(":", 1)[1]; await q.edit_message_text("✅ Til saqlandi. Asosiy menyu:", reply_markup=main_menu(context))


async def create_command(update, context):
    if MINI_APP_URL.startswith("https://"):
        await update.effective_message.reply_text("Test yaratish oynasini ochish uchun tugmani bosing:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧩 Mini App’ni ochish", web_app=WebAppInfo(url=MINI_APP_URL))]]))
    else:
        await update.effective_message.reply_text("Test yaratish oynasi uchun .env faylida MINI_APP_URL HTTPS manzilini ko‘rsating.")


async def language_command(update, context):
    await update.effective_message.reply_text(t(lang(context), "choose_language"), reply_markup=language_keyboard())


async def help_command(update, context):
    await update.effective_message.reply_text("Test yaratish uchun /create.\nUmumiy test uchun /join KOD.\nYakka test uchun /single KOD.\nTayyorgarlik uchun /ready.\nNatijalar: /results KOD.\nPDF: /pdf KOD.\nCSV: /csv KOD.")


async def help_menu(update, context):
    q = update.callback_query; await q.answer(); await q.edit_message_text("Test yaratish tugmasi orqali Mini App oynasini oching.\n/join KOD — umumiy testga kirish.\n/ready — boshlanish oldidan tayyorlikni tasdiqlash.\n/single KOD — doimiy yakka testni darhol boshlash.\n/results KOD va /pdf KOD — natija va PDF.", reply_markup=main_menu(context))


def make_settings(raw, default_pick, question_count):
    mode = raw.get("duration_mode", raw.get("durationMode", "total")); value = safe_int(raw.get("duration_seconds", raw.get("duration", 0)), 0)
    if mode == "total" and "duration_seconds" not in raw: value *= 60
    return {"pick_count": max(1, min(safe_int(raw.get("pick_count", raw.get("pick", default_pick)), default_pick), question_count)), "shuffle_questions": bool(raw.get("shuffle_questions", raw.get("shuffle") in {"both", "questions"})), "shuffle_options": bool(raw.get("shuffle_options", raw.get("shuffle") == "both")), "duration_mode": mode if mode in {"total", "question"} else "total", "duration_seconds": max(0, value), "certificate_enabled": bool(raw.get("certificate_enabled", False)), "certificate_threshold": float(raw.get("certificate_threshold", 0) or 0), "certificate_threshold_type": raw.get("certificate_threshold_type", "points"), "certificate_text": str(raw.get("certificate_text", ""))[:1000], "public_results": bool(raw.get("public_results", False))}


async def web_app_data(update, context):
    message = update.effective_message
    if not message or not message.web_app_data: return
    try:
        payload = json.loads(message.web_app_data.data)
        if payload.get("action") == "written_answer": await receive_written_answer(update, context, payload); return
        if payload.get("action") != "save_test": raise ValueError("unknown action")
        title = str(payload.get("title", "")).strip()[:200]; questions = payload.get("questions") or []; test_type = str(payload.get("type", "quiz"))
        if not title or not (1 <= len(questions) <= 2000) or test_type not in {"quiz", "written", "combined", "single"}: raise ValueError("invalid bank")
        session_info = payload.get("session") or {}; code = str(session_info.get("code", "")).strip() or make_code(8); tz_name = str(session_info.get("timezone") or payload.get("timezone") or DEFAULT_TZ).split(" — ", 1)[0]; ZoneInfo(tz_name)
        start_utc = None
        if test_type != "single":
            local_value = str(session_info.get("start_local", "")).strip()
            if not local_value: raise ValueError("general session needs start_local")
            start_dt = datetime.fromisoformat(local_value).replace(tzinfo=ZoneInfo(tz_name)).astimezone(timezone.utc)
            if start_dt <= now_utc() + timedelta(minutes=5): raise ValueError("start must be at least five minutes ahead")
            start_utc = start_dt.isoformat()
        c = db()
        try:
            c.execute("BEGIN IMMEDIATE")
            bank_id = c.execute("INSERT INTO quiz_banks(creator_id,title,test_type,default_settings) VALUES(?,?,?,?)", (update.effective_user.id, title, test_type, encode(payload))).lastrowid
            quiz_count = written_count = 0
            for pos, item in enumerate(questions):
                body = str(item.get("text", "")).strip(); options = [str(x).strip() for x in (item.get("options") or []) if str(x).strip()]
                if not body: raise ValueError("empty question")
                section = str(item.get("section") or ("written" if test_type == "written" else "quiz")); section = "written" if section == "written" and test_type in {"written", "combined"} else "quiz"
                correct = None
                if section == "quiz":
                    if not 2 <= len(options) <= 4: raise ValueError("quiz needs two to four options")
                    correct = safe_int(item.get("correct"), -1)
                    if not 0 <= correct < len(options): raise ValueError("invalid correct option")
                    quiz_count += 1
                else: written_count += 1
                accepted = item.get("accepted", []); accepted = [x.strip() for x in re.split(r"[,;\n]", accepted) if x.strip()] if isinstance(accepted, str) else accepted
                c.execute("INSERT INTO questions(bank_id,section,body,image_file_id,options_json,correct_index,accepted_answers_json,grading_rules_json,points,position) VALUES(?,?,?,?,?,?,?,?,?,?)", (bank_id, section, body, str(item.get("image_url", item.get("image_file_id", "")) or "").strip()[:1000] or None, encode(options), correct, encode(accepted), encode(item.get("grading_rules", {})), max(0, float(item.get("points", 1) or 1)), pos))
            if (test_type in {"quiz", "single"} and not quiz_count) or (test_type == "written" and not written_count) or (test_type == "combined" and (not quiz_count or not written_count)): raise ValueError("test sections are incomplete")
            quiz_settings = make_settings(payload.get("quiz_settings") or payload, quiz_count or len(questions), quiz_count or len(questions)); written_settings = make_settings(payload.get("written_settings") or payload, written_count or len(questions), written_count or len(questions))
            mode = "single" if test_type == "single" else "general"; state = "running" if mode == "single" else "scheduled"
            session_id = create_session(c, bank_id, update.effective_user.id, code, mode=mode, state=state, timezone=tz_name, start_utc=start_utc, quiz_settings=quiz_settings, written_settings=written_settings, public_results=int(bool(session_info.get("public_results", payload.get("public_results", False)))))
            if mode == "general" and session_info.get("creator_participates"):
                participant_id = create_or_get_participant(c, session_id, update.effective_user.id, update.effective_user.full_name or "Yaratuvchi", update.effective_user.username)
                context.user_data["participant_id"] = participant_id
            c.commit()
        except Exception: c.rollback(); raise
        finally: c.close()
        await message.reply_text(f"✅ Test saqlandi.\nNomi: {escape(title)}\nKod: <code>{escape(code)}</code>\n" + ("Yakka kod doimiy va darhol boshlanadi." if mode == "single" else "Ro‘yxatdan o‘tish uchun /join KOD yuboring. Boshlanish oldidan /ready bosing."), parse_mode=ParseMode.HTML, reply_markup=main_menu(context))
    except Exception as exc:
        log.exception("Mini App payload rejected: %s", type(exc).__name__); await message.reply_text("Mini App ma’lumotlari to‘liq emas yoki noto‘g‘ri. Test turi, savollar, kod va vaqtni tekshiring.", reply_markup=main_menu(context))


async def new_bank(update, context):
    q = update.callback_query; await q.answer()
    if MINI_APP_URL.startswith("https://"): await q.edit_message_text("Test yaratish oynasini ochish uchun tugmani bosing:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧩 Mini App’ni ochish", web_app=WebAppInfo(url=MINI_APP_URL))], [InlineKeyboardButton("⬅️ Menyu", callback_data="back_menu")]]))
    else: await q.edit_message_text("Test yaratish oynasi uchun .env faylida MINI_APP_URL HTTPS manzilini ko‘rsating.", reply_markup=main_menu(context))


async def back_menu(update, context):
    q = update.callback_query; await q.answer(); await q.edit_message_text("Asosiy menyu:", reply_markup=main_menu(context))


async def join_prompt(update, context):
    q = update.callback_query; await q.answer(); context.user_data["join_mode"] = "single" if q.data == "join_single" else "general"; await q.edit_message_text("Test kodini /join KOD ko‘rinishida yuboring.", reply_markup=main_menu(context))


async def join_general_command(update, context): context.user_data["join_mode"] = "general"; await join(update, context)
async def single_command(update, context): context.user_data["join_mode"] = "single"; await join(update, context)


async def join(update, context):
    if not context.args: await update.effective_message.reply_text("Foydalanish: /join TEST_KODI"); return
    code = " ".join(context.args).strip(); c = db(); session = c.execute("SELECT * FROM sessions WHERE code=? AND state NOT IN ('cancelled','finished')", (code,)).fetchone()
    if not session: c.close(); await update.effective_message.reply_text(t(lang(context), "no_test"), reply_markup=main_menu(context)); return
    requested_mode = context.user_data.get("join_mode", "general")
    if requested_mode == "single" and session["mode"] != "single": c.close(); await update.effective_message.reply_text("Bu kod yakka test kodi emas.", reply_markup=main_menu(context)); return
    if requested_mode == "general" and session["mode"] != "general": c.close(); await update.effective_message.reply_text("Bu kod umumiy test kodi emas.", reply_markup=main_menu(context)); return
    if session["mode"] == "general" and session["state"] in {"running", "written"}: c.close(); await update.effective_message.reply_text(t(lang(context), "closed"), reply_markup=main_menu(context)); return
    participant_id = create_or_get_participant(c, session["id"], update.effective_user.id, update.effective_user.full_name or "Ishtirokchi", update.effective_user.username); context.user_data["participant_id"] = participant_id
    if session["mode"] == "single":
        attempt_id = create_attempt(c, session["id"], participant_id, "single", session["bank_id"], decode(session["quiz_settings_json"], {})); c.execute("UPDATE participants SET phase='single', ready=1, started_at=COALESCE(started_at, CURRENT_TIMESTAMP), finished_at=NULL WHERE id=?", (participant_id,)); c.commit(); c.close(); await update.effective_message.reply_text(t(lang(context), "started")); await show_attempt_question(context.bot, update.effective_user.id, attempt_id); return
    c.commit(); c.close(); await update.effective_message.reply_text(f"✅ Testga ro‘yxatdan o‘tdingiz: <code>{escape(session['code'])}</code>\nBoshlanishdan oldingi 5 daqiqada ‘Tayyorman’ tugmasini bosing.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Tayyorman", callback_data=f"ready:{session['id']}")]]))


async def ready(update, context):
    q = update.callback_query
    if q: await q.answer()
    user = update.effective_user; c = db(); session_id = safe_int(q.data.split(":", 1)[1]) if q and q.data.startswith("ready:") else None; participant = c.execute("SELECT * FROM participants WHERE session_id=? AND user_id=?", (session_id, user.id)).fetchone() if session_id else c.execute("SELECT * FROM participants WHERE id=? AND user_id=?", (context.user_data.get("participant_id", 0), user.id)).fetchone()
    if not participant: c.close(); await update.effective_message.reply_text(t(lang(context), "need_join")); return
    c.execute("UPDATE participants SET ready=1 WHERE id=?", (participant["id"],)); c.commit(); c.close(); await (q.message if q else update.effective_message).reply_text(t(lang(context), "ready"))


async def my_tests(update, context):
    q = update.callback_query; await q.answer(); c = db(); rows = c.execute("SELECT * FROM sessions WHERE creator_id=? ORDER BY id DESC LIMIT 30", (update.effective_user.id,)).fetchall(); bank_types = {int(row["id"]): type_for_session(c, row) for row in rows}; c.close()
    if not rows: await q.edit_message_text("Sizda hali testlar yo‘q.", reply_markup=main_menu(context)); return
    await q.edit_message_text("Sizning test sessiyalaringiz:", reply_markup=main_menu(context))
    for row in rows:
        buttons = []
        if row["state"] not in {"finished", "cancelled"}: buttons.append(InlineKeyboardButton("Bekor qilish", callback_data=f"v2cancel:{row['id']}"))
        buttons += [InlineKeyboardButton("Natijalar", callback_data=f"v2results:{row['id']}"), InlineKeyboardButton("PDF", callback_data=f"v2pdf:{row['id']}")]
        if row["mode"] == "general":
            buttons.append(InlineKeyboardButton("Qayta ishga tushirish", callback_data=f"v2rerun:{row['id']}"))
            bank_type = bank_types.get(int(row["id"]), "quiz")
            if row["state"] == "finished" and bank_type == "quiz":
                buttons.append(InlineKeyboardButton("Yakka nusxa yaratish", callback_data=f"v2single:{row['id']}"))
        buttons.append(InlineKeyboardButton("O‘chirish", callback_data=f"v2delete:{row['id']}"))
        await q.message.reply_text(f"📚 <b>{escape(row['code'])}</b> · {escape(row['mode'])} · {escape(row['state'])}", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([buttons]))


async def manage_v2_test(update, context):
    q = update.callback_query; await q.answer(); action, raw = q.data.split(":", 1); session_id = safe_int(raw); c = db(); session = c.execute("SELECT * FROM sessions WHERE id=? AND creator_id=?", (session_id, update.effective_user.id)).fetchone()
    if not session: c.close(); await q.edit_message_text("Sessiya topilmadi."); return
    if action == "v2cancel": c.close(); await q.edit_message_text("Sessiyani bekor qilishni tasdiqlaysizmi? Bank va avvalgi natijalar saqlanadi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ha, bekor qilish", callback_data=f"v2cancel_yes:{session_id}"), InlineKeyboardButton("Yo‘q", callback_data="back_menu")]])); return
    if action == "v2delete": c.close(); await q.edit_message_text("Sessiyani va natijalarini butunlay o‘chirishni tasdiqlaysizmi?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ha, o‘chirish", callback_data=f"v2delete_yes:{session_id}"), InlineKeyboardButton("Yo‘q", callback_data="back_menu")]])); return
    if action == "v2cancel_yes":
        c.execute("UPDATE sessions SET state='cancelled', cancelled_at=? WHERE id=? AND state NOT IN ('finished','cancelled')", (iso_now(), session_id)); users = c.execute("SELECT user_id FROM participants WHERE session_id=?", (session_id,)).fetchall(); c.commit(); c.close()
        for user in users:
            try: await context.bot.send_message(user["user_id"], "⚠️ Yaratuvchi testni bekor qildi. Bu kod endi ishlamaydi.")
            except Exception: log.info("cancel notification failed")
        await q.edit_message_text("✅ Sessiya bekor qilindi. Bank va avvalgi natijalar saqlanadi."); return
    if action == "v2delete_yes": c.execute("DELETE FROM sessions WHERE id=?", (session_id,)); c.commit(); c.close(); await q.edit_message_text("✅ Sessiya va natijalari o‘chirildi."); return
    if action == "v2single":
        bank = c.execute("SELECT * FROM quiz_banks WHERE id=? AND creator_id=?", (int(session["bank_id"]), update.effective_user.id)).fetchone()
        if not bank or bank["test_type"] != "quiz":
            c.close(); await q.edit_message_text("Hozircha yakka nusxa faqat umumiy quiz test uchun mavjud."); return
        try:
            code = make_code(8)
            create_session(c, bank["id"], update.effective_user.id, code, mode="single", state="running", timezone=session["timezone"], start_utc=None, quiz_settings=decode(session["quiz_settings_json"], {}), written_settings=decode(session["written_settings_json"], {}), public_results=0)
            c.commit(); c.close()
            await q.edit_message_text(f"✅ Yakka nusxa yaratildi.\nDoimiy kod: <code>{escape(code)}</code>\nKod kiritilishi bilan test darhol boshlanadi.", parse_mode=ParseMode.HTML, reply_markup=main_menu(context))
            return
        except Exception:
            c.rollback(); c.close(); await q.edit_message_text("Yakka nusxa yaratib bo‘lmadi. Qayta urinib ko‘ring."); return
    if action == "v2rerun":
        bank = c.execute("SELECT * FROM quiz_banks WHERE id=? AND creator_id=?", (int(session["bank_id"]), update.effective_user.id)).fetchone()
        if not bank: c.close(); await q.edit_message_text("Savollar banki topilmadi."); return
        try:
            mode = "single" if bank["test_type"] == "single" else "general"; new_start = None if mode == "single" else (now_utc() + timedelta(minutes=10)).isoformat(); code = make_code(8)
            create_session(c, bank["id"], update.effective_user.id, code, mode=mode, state="running" if mode == "single" else "scheduled", timezone=session["timezone"], start_utc=new_start, quiz_settings=decode(session["quiz_settings_json"], {}), written_settings=decode(session["written_settings_json"], {}), public_results=session["public_results"]); c.commit(); c.close(); await q.edit_message_text(f"✅ Yangi sessiya yaratildi. Kod: <code>{escape(code)}</code>", parse_mode=ParseMode.HTML); return
        except Exception: c.rollback(); c.close(); await q.edit_message_text("Yangi kod yaratib bo‘lmadi."); return
    c.close()


async def show_attempt_question(bot, user_id, attempt_id):
    c = db(); attempt = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not attempt or attempt["finished_at"]: c.close(); return
    session = c.execute("SELECT * FROM sessions WHERE id=?", (attempt["session_id"],)).fetchone(); question = current_attempt_question(c, attempt_id)
    if not session or not question:
        if attempt and not attempt["finished_at"]: finish_attempt(c, attempt_id)
        c.commit(); c.close(); await send_attempt_result(bot, user_id, attempt_id); return
    settings = settings_for(session, attempt["phase"])
    if settings.get("duration_mode") == "question" and settings.get("duration_seconds"): c.execute("UPDATE attempts SET deadline_at=? WHERE id=? AND current_position=?", ((now_utc() + timedelta(seconds=int(settings["duration_seconds"]))).isoformat(), attempt_id, attempt["current_position"])); c.commit()
    options = decode(question["options_json"], []); order = decode(question["options_order_json"], list(range(len(options)))); image = question["image_file_id"]; position = int(attempt["current_position"]) + 1; c.close()
    if image:
        try: await bot.send_photo(user_id, photo=image)
        except Exception: log.info("question image could not be sent")
    if attempt["phase"] == "written":
        url = f"{MINI_APP_URL}/answer?attempt_id={attempt_id}&question_id={question['question_id']}" if MINI_APP_URL.startswith("https://") else ""; kb = InlineKeyboardMarkup([[InlineKeyboardButton("✍️ Javobni Mini App oynasida yozish", web_app=WebAppInfo(url=url))]]) if url else None; await bot.send_message(user_id, f"Savol {position}:\n\n{question['body']}", reply_markup=kb); return
    buttons = [[InlineKeyboardButton(f"{LETTERS[display]}. {str(options[original])[:80]}", callback_data=f"v2ans:{attempt_id}:{question['question_id']}:{display}")] for display, original in enumerate(order) if display < len(LETTERS)]; await bot.send_message(user_id, f"Savol {position}:\n\n{question['body']}", reply_markup=InlineKeyboardMarkup(buttons))


async def answer_v2(update, context):
    q = update.callback_query; await q.answer()
    try: _, attempt_raw, question_raw, selected_raw = q.data.split(":"); attempt_id, question_id, selected_display = int(attempt_raw), int(question_raw), int(selected_raw)
    except (ValueError, AttributeError): return
    c = db(); row = c.execute("SELECT a.*, p.user_id, s.state FROM attempts a JOIN participants p ON p.id=a.participant_id JOIN sessions s ON s.id=a.session_id WHERE a.id=?", (attempt_id,)).fetchone(); current = current_attempt_question(c, attempt_id)
    if not row or row["user_id"] != update.effective_user.id or row["finished_at"] or row["phase"] not in {"quiz", "single"} or not current or int(current["question_id"]) != question_id or row["state"] not in {"running", "written"}: c.close(); return
    if c.execute("SELECT 1 FROM answers WHERE attempt_id=? AND question_id=?", (attempt_id, question_id)).fetchone(): c.close(); await q.edit_message_reply_markup(reply_markup=None); return
    options = decode(current["options_json"], []); order = decode(current["options_order_json"], list(range(len(options))))
    if not 0 <= selected_display < len(order): c.close(); return
    original_index = int(order[selected_display]); correct = int(current["correct_index"] is not None and original_index == int(current["correct_index"])); points = float(current["points"] or 0) if correct else 0
    c.execute("INSERT INTO answers(attempt_id,question_id,selected_index,is_correct,awarded_points) VALUES(?,?,?,?,?)", (attempt_id, question_id, original_index, correct, points)); c.execute("UPDATE attempts SET correct=correct+?, wrong=wrong+?, total_points=total_points+?, current_position=current_position+1 WHERE id=?", (correct, 1 - correct, points, attempt_id)); ended = current_attempt_question(c, attempt_id) is None
    if ended: finish_attempt(c, attempt_id)
    c.commit(); c.close()
    try: await q.edit_message_reply_markup(reply_markup=None)
    except Exception: pass
    if ended:
        if row["phase"] == "single": await send_attempt_result(context.bot, update.effective_user.id, attempt_id)
        else: await context.bot.send_message(update.effective_user.id, "✅ Bu qism yakunlandi. Yakuniy natijani kuting.")
    else: await show_attempt_question(context.bot, update.effective_user.id, attempt_id)


async def receive_written_answer(update, context, payload):
    attempt_id = safe_int(payload.get("attempt_id")); question_id = safe_int(payload.get("question_id")); text = str(payload.get("answer", "")).strip(); c = db(); row = c.execute("SELECT a.*, p.user_id, s.state FROM attempts a JOIN participants p ON p.id=a.participant_id JOIN sessions s ON s.id=a.session_id WHERE a.id=?", (attempt_id,)).fetchone(); current = current_attempt_question(c, attempt_id)
    if not row or row["user_id"] != update.effective_user.id or row["finished_at"] or row["phase"] not in {"written", "single"} or not current or int(current["question_id"]) != question_id or row["state"] not in {"running", "written"}: c.close(); await update.effective_message.reply_text("Bu yozma savol endi faol emas."); return
    if c.execute("SELECT 1 FROM answers WHERE attempt_id=? AND question_id=?", (attempt_id, question_id)).fetchone(): c.close(); await update.effective_message.reply_text("Bu savolga javob allaqachon qabul qilingan."); return
    accepted = decode(current["accepted_answers_json"], []); rules = decode(current["grading_rules_json"], {}); correct = int(check_written_answer(text, accepted, rules=rules)) if text else 0; points = float(current["points"] or 0) if correct else 0
    c.execute("INSERT INTO answers(attempt_id,question_id,answer_text,is_correct,awarded_points) VALUES(?,?,?,?,?)", (attempt_id, question_id, text, correct, points)); c.execute("UPDATE attempts SET correct=correct+?, wrong=wrong+?, total_points=total_points+?, current_position=current_position+1 WHERE id=?", (correct, 1 - correct, points, attempt_id)); ended = current_attempt_question(c, attempt_id) is None
    if ended: finish_attempt(c, attempt_id)
    c.commit(); c.close()
    if ended: await update.effective_message.reply_text("✅ Yozma qism yakunlandi. Natija tayyorlanmoqda."); await send_attempt_result(context.bot, update.effective_user.id, attempt_id)
    else: await update.effective_message.reply_text(t(lang(context), "accepted")); await show_attempt_question(context.bot, update.effective_user.id, attempt_id)


async def written_answer_legacy(update, context): await update.effective_message.reply_text(t(lang(context), "written_only"))


def result_rows(c, attempt_id): return c.execute("SELECT aq.sequence_no, q.body, q.options_json, q.correct_index, q.accepted_answers_json, a.selected_index, a.answer_text, a.is_correct FROM attempt_questions aq JOIN questions q ON q.id=aq.question_id LEFT JOIN answers a ON a.attempt_id=aq.attempt_id AND a.question_id=aq.question_id WHERE aq.attempt_id=? ORDER BY aq.sequence_no", (attempt_id,)).fetchall()


async def send_attempt_result(bot, user_id, attempt_id):
    c = db(); attempt = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not attempt: c.close(); return
    session = c.execute("SELECT * FROM sessions WHERE id=?", (attempt["session_id"],)).fetchone(); total = c.execute("SELECT COUNT(*) AS n FROM attempt_questions WHERE attempt_id=?", (attempt_id,)).fetchone()["n"]; percentage = float(attempt["correct"]) / total * 100 if total else 0; lines = [f"🏁 Natija\nTo‘g‘ri: {int(attempt['correct'])}\nXato: {int(attempt['wrong'])}\nJavobsiz: {int(attempt['unanswered'] or 0)}\nFoiz: {percentage:.1f}%\nBall: {attempt['total_points']}", "", "📖 Ko‘rib chiqish:"]
    for r in result_rows(c, attempt_id):
        selected = LETTERS[r["selected_index"]] if r["selected_index"] is not None and r["selected_index"] < len(LETTERS) else (r["answer_text"] or "javobsiz"); correct = LETTERS[r["correct_index"]] if r["correct_index"] is not None else ", ".join(decode(r["accepted_answers_json"], [])); lines.append(f"{r['sequence_no'] + 1}. {r['body']}\nSizning javobingiz: {selected}\nTo‘g‘ri javob: {correct}")
    c.close(); text = "\n\n".join(lines)
    for start in range(0, len(text), 3800): await bot.send_message(user_id, text[start:start + 3800])
    if session and session["mode"] == "general": await maybe_send_combined_result(bot, user_id, attempt_id)


async def maybe_send_combined_result(bot, user_id, attempt_id):
    c = db(); attempt = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not attempt: c.close(); return
    session = c.execute("SELECT * FROM sessions WHERE id=?", (attempt["session_id"],)).fetchone()
    if type_for_session(c, session) != "combined": c.close(); return
    other = c.execute("SELECT * FROM attempts WHERE participant_id=? AND phase='quiz' AND finished_at IS NOT NULL ORDER BY id DESC LIMIT 1", (attempt["participant_id"],)).fetchone()
    if other:
        qtotal = c.execute("SELECT COUNT(*) AS n FROM attempt_questions WHERE attempt_id=?", (other["id"],)).fetchone()["n"]; wtotal = c.execute("SELECT COUNT(*) AS n FROM attempt_questions WHERE attempt_id=?", (attempt_id,)).fetchone()["n"]; total = qtotal + wtotal; correct = float(other["correct"]) + float(attempt["correct"]); points = float(other["total_points"]) + float(attempt["total_points"]); c.close(); await bot.send_message(user_id, f"🏆 Umumiy natija\nQuiz: {int(other['correct'])}/{qtotal}\nYozma: {int(attempt['correct'])}/{wtotal}\nJami: {int(correct)}/{total} ({(correct / total * 100) if total else 0:.1f}%)\nJami ball: {points}")
    else: c.close()


async def send_certificate_if_enabled(bot, c, session, participant):
    bank = c.execute("SELECT * FROM quiz_banks WHERE id=?", (session["bank_id"],)).fetchone()
    if not bank: return
    settings = decode(bank["default_settings"], {})
    if not settings.get("certificate_enabled"): return
    attempt = c.execute("SELECT * FROM attempts WHERE participant_id=? AND finished_at IS NOT NULL ORDER BY total_points DESC, correct DESC LIMIT 1", (participant["id"],)).fetchone()
    if not attempt: return
    total = c.execute("SELECT COUNT(*) AS n FROM attempt_questions WHERE attempt_id=?", (attempt["id"],)).fetchone()["n"]; percent = float(attempt["correct"]) / total * 100 if total else 0; threshold = float(settings.get("certificate_threshold", 0) or 0); qualifies = percent >= threshold if settings.get("certificate_threshold_type") == "percent" else float(attempt["total_points"]) >= threshold
    if not qualifies: return
    existing = c.execute("SELECT * FROM certificates WHERE session_id=? AND participant_id=?", (session["id"], participant["id"])).fetchone()
    if existing and existing["sent_at"]: return
    path = Path("pdf_exports") / f"certificate_{session['id']}_{participant['id']}.pdf"; build_certificate(path, participant["display_name"], bank["title"], f"{attempt['total_points']} ball", now_utc().strftime("%Y-%m-%d"), settings.get("certificate_text", "")); c.execute("INSERT OR IGNORE INTO certificates(session_id,participant_id,pdf_path) VALUES(?,?,?)", (session["id"], participant["id"], str(path))); c.commit()
    try:
        with path.open("rb") as fh: await bot.send_document(participant["user_id"], document=fh, filename=path.name, caption="🎓 Diplom/sertifikatingiz tayyor.")
        c.execute("UPDATE certificates SET sent_at=? WHERE session_id=? AND participant_id=?", (iso_now(), session["id"], participant["id"])); c.commit()
    except Exception: log.exception("certificate delivery failed")


async def scheduler_tick(context):
    now = now_utc(); c = db(); sessions = c.execute("SELECT * FROM sessions WHERE state IN ('scheduled','ready','running','written')").fetchall()
    for session in sessions:
        bank_type = type_for_session(c, session)
        if session["mode"] == "general":
            start = parse_utc(session["start_utc"])
            if not start: continue
            diff = (start - now).total_seconds()
            if session["state"] == "scheduled" and 0 < diff <= 300:
                c.execute("UPDATE sessions SET state='ready' WHERE id=? AND state='scheduled'", (session["id"],))
                for p in c.execute("SELECT user_id FROM participants WHERE session_id=? AND ready=1", (session["id"],)).fetchall():
                    try: await context.bot.send_message(p["user_id"], "⏳ Test 5 daqiqalik tayyorgarlik bosqichida.")
                    except Exception: pass
            if diff <= 0 and session["state"] in {"scheduled", "ready"}:
                phase = "quiz" if bank_type in {"quiz", "combined"} else "written"; c.execute("UPDATE sessions SET state='running' WHERE id=? AND state IN ('scheduled','ready')", (session["id"],)); settings = settings_for(session, phase)
                for p in c.execute("SELECT * FROM participants WHERE session_id=? AND ready=1", (session["id"],)).fetchall():
                    c.execute("UPDATE participants SET phase=?, started_at=COALESCE(started_at,CURRENT_TIMESTAMP) WHERE id=?", (phase, p["id"])); attempt_id = create_attempt(c, session["id"], p["id"], phase, session["bank_id"], settings)
                    try: await context.bot.send_message(p["user_id"], t("uz", "started")); await show_attempt_question(context.bot, p["user_id"], attempt_id)
                    except Exception: log.info("start notification failed")
            diff = (start - now).total_seconds()
        else:
            diff = None
        # Every open attempt, including permanent single tests, is checked on every tick.
        open_attempts = c.execute("SELECT a.*, p.user_id FROM attempts a JOIN participants p ON p.id=a.participant_id WHERE a.session_id=? AND a.finished_at IS NULL", (session["id"],)).fetchall()
        for attempt in open_attempts:
            deadline = parse_utc(attempt["deadline_at"])
            if not deadline or deadline > now: continue
            total = c.execute("SELECT COUNT(*) AS n FROM attempt_questions WHERE attempt_id=?", (attempt["id"],)).fetchone()["n"]; remaining = max(1, total - int(attempt["current_position"]))
            current = current_attempt_question(c, attempt["id"])
            settings = settings_for(session, attempt["phase"])
            if settings.get("duration_mode") == "question":
                if current: c.execute("INSERT OR IGNORE INTO answers(attempt_id,question_id,is_correct,awarded_points) VALUES(?,?,?,?)", (attempt["id"], current["question_id"], 0, 0))
                c.execute("UPDATE attempts SET unanswered=unanswered+1,current_position=current_position+1,deadline_at=NULL WHERE id=?", (attempt["id"],))
                if current_attempt_question(c, attempt["id"]) is None: finish_attempt(c, attempt["id"])
                c.commit(); await show_attempt_question(context.bot, attempt["user_id"], attempt["id"])
            else:
                c.execute("UPDATE attempts SET unanswered=unanswered+?,current_position=?,deadline_at=NULL WHERE id=?", (remaining, total, attempt["id"])); finish_attempt(c, attempt["id"]); c.commit()
                if session["mode"] == "single": await send_attempt_result(context.bot, attempt["user_id"], attempt["id"])
        if session["mode"] != "general": continue
        quiz_duration = safe_int(settings_for(session, "quiz").get("duration_seconds"), 0)
        if session["state"] == "running" and quiz_duration and diff is not None and diff <= -quiz_duration:
            if bank_type == "combined":
                c.execute("UPDATE sessions SET state='written', written_ready_at=? WHERE id=? AND state='running'", ((now + timedelta(seconds=10)).isoformat(), session["id"]))
                for p in c.execute("SELECT * FROM participants WHERE session_id=?", (session["id"],)).fetchall():
                    for a in c.execute("SELECT id FROM attempts WHERE participant_id=? AND phase='quiz' AND finished_at IS NULL", (p["id"],)).fetchall(): finish_attempt(c, a["id"])
                    c.execute("UPDATE participants SET phase='written' WHERE id=?", (p["id"],))
                    try: await context.bot.send_message(p["user_id"], "⏳ Quiz tugadi. Yozma qism 10 soniyadan so‘ng boshlanadi.")
                    except Exception: pass
            else:
                c.execute("UPDATE sessions SET state='finished' WHERE id=? AND state='running'", (session["id"],))
                for p in c.execute("SELECT * FROM participants WHERE session_id=?", (session["id"],)).fetchall():
                    for a in c.execute("SELECT id FROM attempts WHERE participant_id=? AND finished_at IS NULL", (p["id"],)).fetchall(): finish_attempt(c, a["id"])
                    latest = c.execute("SELECT id FROM attempts WHERE participant_id=? ORDER BY id DESC LIMIT 1", (p["id"],)).fetchone()
                    try:
                        await context.bot.send_message(p["user_id"], t("uz", "finished"))
                        if latest: await send_attempt_result(context.bot, p["user_id"], latest["id"])
                    except Exception: pass
                    await send_certificate_if_enabled(context.bot, c, session, p)
        if session["state"] == "written":
            ready_at = parse_utc(session["written_ready_at"])
            if ready_at and now >= ready_at:
                c.execute("UPDATE sessions SET written_ready_at=NULL WHERE id=? AND written_ready_at IS NOT NULL", (session["id"],)); settings = settings_for(session, "written")
                for p in c.execute("SELECT * FROM participants WHERE session_id=?", (session["id"],)).fetchall():
                    attempt = c.execute("SELECT id FROM attempts WHERE participant_id=? AND phase='written' ORDER BY id DESC LIMIT 1", (p["id"],)).fetchone(); attempt_id = attempt["id"] if attempt else create_attempt(c, session["id"], p["id"], "written", session["bank_id"], settings)
                    try: await context.bot.send_message(p["user_id"], "✍️ Yozma qism boshlandi!"); await show_attempt_question(context.bot, p["user_id"], attempt_id)
                    except Exception: pass
            written_duration = safe_int(settings_for(session, "written").get("duration_seconds"), 0)
            if written_duration and diff is not None and diff <= -(quiz_duration + 10 + written_duration):
                c.execute("UPDATE sessions SET state='finished' WHERE id=? AND state='written'", (session["id"],))
                for p in c.execute("SELECT * FROM participants WHERE session_id=?", (session["id"],)).fetchall():
                    for a in c.execute("SELECT id FROM attempts WHERE participant_id=? AND phase='written' AND finished_at IS NULL", (p["id"],)).fetchall(): finish_attempt(c, a["id"])
                    try: await context.bot.send_message(p["user_id"], "🏁 Yozma bosqich va umumiy test yakunlandi.")
                    except Exception: pass
                    await send_certificate_if_enabled(context.bot, c, session, p)
    c.commit(); c.close()


async def results_for_session(update, context, session_id):
    c = db(); session = c.execute("SELECT * FROM sessions WHERE id=? AND creator_id=?", (session_id, update.effective_user.id)).fetchone()
    if not session: c.close(); await update.effective_message.reply_text("Sessiya topilmadi yoki siz yaratuvchi emassiz."); return
    rows = c.execute("SELECT p.*, MAX(a.total_points) AS best_points, MAX(a.correct) AS best_correct FROM participants p LEFT JOIN attempts a ON a.participant_id=p.id AND a.finished_at IS NOT NULL WHERE p.session_id=? GROUP BY p.id ORDER BY best_points DESC, best_correct DESC, p.id ASC", (session_id,)).fetchall(); c.close()
    if not rows: await update.effective_message.reply_text(t(lang(context), "no_results")); return
    lines = [f"🏆 {session['code']} reytingi"]; last = None; rank = 0
    for index, row in enumerate(rows, 1):
        score = (row["best_points"] or 0, row["best_correct"] or 0)
        if score != last: rank = index; last = score
        profile = f"https://t.me/{row['username']}" if row["username"] else "profil havolasi yo‘q"; lines.append(f"{rank}. {escape(row['display_name'])} — {row['best_points'] or 0} ball — {profile}")
    await update.effective_message.reply_text("\n".join(lines)[:4000], parse_mode=ParseMode.HTML)


async def results_command(update, context):
    if not context.args: await update.effective_message.reply_text("Foydalanish: /results TEST_KODI"); return
    code = " ".join(context.args).strip(); c = db(); session = c.execute("SELECT * FROM sessions WHERE code=?", (code,)).fetchone()
    if not session: c.close(); await update.effective_message.reply_text("Test topilmadi."); return
    if session["creator_id"] != update.effective_user.id and not session["public_results"]:
        participant = c.execute("SELECT id FROM participants WHERE session_id=? AND user_id=?", (session["id"], update.effective_user.id)).fetchone()
        if not participant: c.close(); await update.effective_message.reply_text("Bu natijalar faqat ruxsat berilgan foydalanuvchiga ko‘rinadi."); return
    rows = c.execute("SELECT p.*, MAX(a.total_points) AS best_points, MAX(a.correct) AS best_correct FROM participants p LEFT JOIN attempts a ON a.participant_id=p.id AND a.finished_at IS NOT NULL WHERE p.session_id=? GROUP BY p.id ORDER BY best_points DESC, best_correct DESC, p.id ASC", (session["id"],)).fetchall(); c.close()
    if not rows: await update.effective_message.reply_text(t(lang(context), "no_results")); return
    lines = [f"🏆 {session['code']} reytingi"]; last = None; rank = 0
    for index, row in enumerate(rows, 1):
        score = (row["best_points"] or 0, row["best_correct"] or 0)
        if score != last: rank = index; last = score
        profile = f"https://t.me/{row['username']}" if row["username"] else "profil havolasi yo‘q"; lines.append(f"{rank}. {escape(row['display_name'])} — {row['best_points'] or 0} ball — {profile}")
    await update.effective_message.reply_text("\n".join(lines)[:4000], parse_mode=ParseMode.HTML)


async def pdf_for_session(update, context, session_id=None):
    c = db(); session = c.execute("SELECT * FROM sessions WHERE id=? AND creator_id=?", (session_id, update.effective_user.id)).fetchone() if session_id else c.execute("SELECT * FROM sessions WHERE code=? AND creator_id=?", (" ".join(context.args).strip() if context.args else "", update.effective_user.id)).fetchone()
    if not session: c.close(); await update.effective_message.reply_text("Test topilmadi yoki siz yaratuvchi emassiz."); return
    bank = c.execute("SELECT * FROM quiz_banks WHERE id=?", (session["bank_id"],)).fetchone(); questions = c.execute("SELECT * FROM questions WHERE bank_id=? ORDER BY position", (session["bank_id"],)).fetchall(); c.close(); items = []
    for q in questions: items.append({"text": q["body"], "options": decode(q["options_json"], []), "correct_answer": LETTERS[q["correct_index"]] if q["correct_index"] is not None else ", ".join(decode(q["accepted_answers_json"], [])), "points": q["points"]})
    path = Path("pdf_exports") / f"test_{session['id']}_{session['code']}.pdf"; build_test_pdf(path, bank["title"], items, kind="written" if bank["test_type"] == "written" else "quiz", answers="hidden")
    with path.open("rb") as fh: await update.effective_message.reply_document(document=fh, filename=path.name, caption="📄 Test PDF fayli")


async def pdf_command(update, context): await pdf_for_session(update, context)


async def csv_command(update, context):
    if not context.args: await update.effective_message.reply_text("Foydalanish: /csv TEST_KODI"); return
    c = db(); session = c.execute("SELECT * FROM sessions WHERE code=? AND creator_id=?", (" ".join(context.args).strip(), update.effective_user.id)).fetchone()
    if not session: c.close(); await update.effective_message.reply_text("Test topilmadi yoki siz yaratuvchi emassiz."); return
    rows = c.execute("SELECT p.display_name,p.username,a.phase,a.correct,a.wrong,a.unanswered,a.total_points,a.finished_at FROM participants p JOIN attempts a ON a.participant_id=p.id WHERE p.session_id=? AND a.finished_at IS NOT NULL ORDER BY a.total_points DESC", (session["id"],)).fetchall(); c.close(); output = io.StringIO(); writer = csv.writer(output); writer.writerow(["Ism", "Username", "Qism", "To‘g‘ri", "Xato", "Javobsiz", "Ball", "Yakunlangan vaqt"])
    for r in rows: writer.writerow(list(r))
    bio = io.BytesIO(output.getvalue().encode("utf-8-sig")); bio.name = f"results_{session['code']}.csv"; await update.effective_message.reply_document(document=bio, caption="📊 Natijalar CSV fayli")


async def error(update, context):
    if context.error: log.exception("Telegram update error", exc_info=context.error)


async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Botni boshlash"), BotCommand("create", "Test yaratish"), BotCommand("join", "Umumiy testga kirish"),
        BotCommand("single", "Yakka test ishlash"), BotCommand("ready", "Tayyorman"), BotCommand("results", "Natijalarni ko‘rish"),
        BotCommand("pdf", "Test PDF fayli"), BotCommand("csv", "Natijalar CSV fayli"), BotCommand("language", "Tilni tanlash"), BotCommand("help", "Yordam"),
    ])
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


def build_app():
    if not TOKEN: raise RuntimeError("BOT_TOKEN .env faylida ko‘rsatilmagan")
    init_schema(DB_PATH); app = Application.builder().token(TOKEN).post_init(post_init).build(); app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("create", create_command)); app.add_handler(CommandHandler("join", join_general_command)); app.add_handler(CommandHandler("single", single_command)); app.add_handler(CommandHandler("ready", ready)); app.add_handler(CommandHandler("wanswer", written_answer_legacy)); app.add_handler(CommandHandler("results", results_command)); app.add_handler(CommandHandler("pdf", pdf_command)); app.add_handler(CommandHandler("csv", csv_command)); app.add_handler(CommandHandler("language", language_command)); app.add_handler(CommandHandler("help", help_command)); app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data)); app.add_handler(CallbackQueryHandler(language_list, pattern="^languages$")); app.add_handler(CallbackQueryHandler(set_language, pattern="^setlang:")); app.add_handler(CallbackQueryHandler(new_bank, pattern="^new_bank$")); app.add_handler(CallbackQueryHandler(back_menu, pattern="^back_menu$")); app.add_handler(CallbackQueryHandler(join_prompt, pattern="^join_(general|single)$")); app.add_handler(CallbackQueryHandler(ready, pattern="^ready:")); app.add_handler(CallbackQueryHandler(my_tests, pattern="^my_tests$")); app.add_handler(CallbackQueryHandler(manage_v2_test, pattern="^v2(cancel|delete|cancel_yes|delete_yes|rerun|single):")); app.add_handler(CallbackQueryHandler(lambda u, c: pdf_for_session(u, c, safe_int(u.callback_query.data.split(":", 1)[1])), pattern="^v2pdf:")); app.add_handler(CallbackQueryHandler(lambda u, c: results_for_session(u, c, safe_int(u.callback_query.data.split(":", 1)[1])), pattern="^v2results:")); app.add_handler(CallbackQueryHandler(answer_v2, pattern="^v2ans:")); app.add_error_handler(error); app.job_queue.run_repeating(scheduler_tick, interval=1, first=1); return app


if __name__ == "__main__": build_app().run_polling(allowed_updates=Update.ALL_TYPES)
