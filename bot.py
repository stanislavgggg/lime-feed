"""
bot.py — Kinetic Feed (news & live scores)
Commands: /start /news /live /today /lang /policy /join
"""
import asyncio, logging, os, sys, atexit, time
from telegram import Update
from telegram.error import Conflict, NetworkError
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode
from config import BOT_TOKEN, BOT_USERNAME, HOOK_IMAGE, State, TG_LANG_MAP, DEFAULT_LANG
from brand import BRAND
from storage import get_user, update_user, append_history
from conversation import (
    handle_message, handle_menu_action, main_menu,
    send_channel_join, handle_join_check, JOIN_CHECK_CB,
    handle_news, handle_news_callback, NEWS_CB_PREFIX,
)
from messages import HOOK_CAPTION
from media import send_pic, pics_available
import analytics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

LOCK_FILE = "/tmp/metaplay_bot.lock"

def _check_lock():
    if os.path.exists(LOCK_FILE):
        try:
            pid = int(open(LOCK_FILE).read().strip())
            os.kill(pid, 0)
            logger.critical(f"Already running (PID {pid}). Exiting.")
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            os.remove(LOCK_FILE)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))

_check_lock()

def _detect_lang(code):
    if not code:
        return DEFAULT_LANG
    return TG_LANG_MAP.get(code.split("-")[0].lower(), DEFAULT_LANG)

def _admin_ids():
    raw = os.environ.get("ADMIN_IDS", "")
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


# ── /start ────────────────────────────────────────────────────────────────────
# Visible privacy + 18+ disclaimer appended to the very first screen every user
# (and every ad-moderation reviewer) sees. Plain text + bare URL so it renders
# correctly under BOTH Markdown and HTML parse modes. URL matches /policy.
PRIVACY_URL = BRAND.privacy_url or "https://arenafronend.s26636274.workers.dev/privacy"
# Primary /start path (send_pic) renders Markdown → use a [text](url) hyperlink
# so the raw URL is hidden behind clean tappable text.
START_LEGAL_FOOTER = {
    "en": f"\n\n———\n18+ · Informational only, not betting/financial advice.\n[Privacy Policy]({PRIVACY_URL})",
    "es": f"\n\n———\n18+ · Solo información, no es asesoramiento de apuestas/financiero.\n[Política de Privacidad]({PRIVACY_URL})",
    "ru": f"\n\n———\n18+ · Только информация, не беттинг/финансовый совет.\n[Политика конфиденциальности]({PRIVACY_URL})",
}
# Fallback /start path (hook.png) renders HTML → matching <a href> hyperlink.
START_LEGAL_FOOTER_HTML = {
    "en": f'\n\n———\n18+ · Informational only, not betting/financial advice.\n<a href="{PRIVACY_URL}">Privacy Policy</a>',
    "es": f'\n\n———\n18+ · Solo información, no es asesoramiento de apuestas/financiero.\n<a href="{PRIVACY_URL}">Política de Privacidad</a>',
    "ru": f'\n\n———\n18+ · Только информация, не беттинг/финансовый совет.\n<a href="{PRIVACY_URL}">Политика конфиденциальности</a>',
}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    detected = _detect_lang(user.language_code)
    u_check  = get_user(user.id, detected)
    # Respect an explicit choice (/lang or the mini-app switcher). Telegram often
    # keeps sending a stale language_code, so /start must NOT clobber a manual pick.
    lang = (u_check.get("lang", detected)
            if u_check.get("lang_manual") else detected)

    # Deep link `/start join` → нативный канальный CTA с верификацией подписки.
    # Мини-апп проксирует тап «подписаться» сюда (t.me/<bot>?start=join), чтобы
    # вся конверсия шла внутри Telegram одним потоком, без выхода в вебвью.
    if context.args and context.args[0].lower() == "join":
        update_user(user.id, lang=lang)
        await send_channel_join(context.bot, chat_id, lang)
        logger.info(f"/start join user={user.id} lang={lang}")
        return

    is_new = u_check.get("message_count", 0) == 0
    if is_new:
        update_user(user.id, lang=lang, state=State.NEW,
                    onboarding_done=False, onboarding_turn=0, stage_replies=0)
    else:
        update_user(user.id, lang=lang)
    caption = HOOK_CAPTION.get(lang, HOOK_CAPTION["en"])
    caption = caption + START_LEGAL_FOOTER.get(lang, START_LEGAL_FOOTER["en"])
    menu    = main_menu(lang)
    # Try branded image first (pics/19.png), then hook.png, then text
    sent = await send_pic(context.bot, chat_id, "start", caption, lang, reply_markup=menu)
    if not sent and os.path.exists(HOOK_IMAGE):
        # HTML fallback path: swap the Markdown footer for the HTML hyperlink one.
        caption_html = (HOOK_CAPTION.get(lang, HOOK_CAPTION["en"])
                        + START_LEGAL_FOOTER_HTML.get(lang, START_LEGAL_FOOTER_HTML["en"]))
        try:
            with open(HOOK_IMAGE, "rb") as p:
                await context.bot.send_photo(
                    chat_id=chat_id, photo=p,
                    caption=caption_html, parse_mode=ParseMode.HTML,
                    reply_markup=menu,
                )
            sent = True
        except Exception as e:
            logger.warning(f"Hook image fallback: {e}")
    append_history(user.id, "assistant", caption)
    logger.info(f"/start user={user.id} lang={lang}")


# ── Menu command shortcuts ────────────────────────────────────────────────────

async def _menu(action, update, context):
    user  = update.effective_user
    u     = get_user(user.id)
    lang  = u.get("lang", _detect_lang(user.language_code))
    try:
        await handle_menu_action(context.bot, user.id, update.effective_chat.id, lang, action)
    except Exception as e:
        logger.error(f"_menu crashed action={action} user={user.id}: {e}", exc_info=True)
        err = "⚠️ Algo salió mal — intentá de nuevo." if lang == "es" else "⚠️ Something went wrong — try again in a moment."
        try:
            await update.message.reply_text(err)
        except Exception:
            pass

async def cmd_live(u, c):  await _menu("live",  u, c)
async def cmd_today(u, c): await _menu("today", u, c)


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u    = get_user(user.id)
    lang = u.get("lang", _detect_lang(user.language_code))
    try:
        await handle_news(context.bot, user.id, update.effective_chat.id, lang)
    except Exception as e:
        logger.error(f"cmd_news crashed user={user.id}: {e}", exc_info=True)


async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/lang en|ru|es — explicitly set content language (overrides auto-detect).

    The bot already re-detects language from Telegram on every /start, but this
    gives the user deterministic control if Telegram reports a stale language_code.
    """
    user = update.effective_user
    arg = (context.args[0].lower() if context.args else "")
    valid = ("en", "ru", "es")
    if arg in valid:
        update_user(user.id, lang=arg, lang_manual=True)
        msg = {
            "en": "✅ Language set to English. (Stays fixed — use /lang to change.)",
            "ru": "✅ Язык переключён на русский. (Закреплён — сменить через /lang.)",
            "es": "✅ Idioma cambiado a español. (Fijado — usa /lang para cambiar.)",
        }[arg]
        await update.message.reply_text(msg)
        logger.info("lang set user=%s -> %s (manual)", user.id, arg)
    else:
        cur = get_user(user.id).get("lang", _detect_lang(user.language_code))
        await update.message.reply_text(
            f"🌐 Current language: {cur.upper()}\n"
            "Usage: /lang en · /lang ru · /lang es"
        )


async def cmd_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u    = get_user(update.effective_user.id)
    lang = u.get("lang", _detect_lang(update.effective_user.language_code))
    if lang == "es":
        text = (
            "🔒 *Política de Privacidad*\n\n"
            f"{BRAND.display_name} recopila únicamente tu ID de Telegram para personalizar el feed.\n"
            "No almacenamos datos de pago ni información personal sensible.\n\n"
            f"[Leer política completa →]({PRIVACY_URL})"
        )
    elif lang == "ru":
        text = (
            "🔒 *Политика конфиденциальности*\n\n"
            f"{BRAND.display_name} собирает только твой Telegram ID для персонализации ленты.\n"
            "Мы не храним платёжные данные и чувствительную личную информацию.\n\n"
            f"[Читать полностью →]({PRIVACY_URL})"
        )
    else:
        text = (
            "🔒 *Privacy Policy*\n\n"
            f"{BRAND.display_name} collects only your Telegram ID to personalise the feed.\n"
            "We don't store payment data or sensitive personal information.\n\n"
            f"[Read full policy →]({PRIVACY_URL})"
        )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ── Text messages ─────────────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()
    if not text:
        return
    u    = get_user(user.id)
    lang = u.get("lang", _detect_lang(user.language_code))
    try:
        await handle_message(context.bot, user.id, update.effective_chat.id, text, lang)
    except Exception as e:
        logger.error(f"handle_text crashed user={user.id} text={text[:40]!r}: {e}", exc_info=True)
        err = "⚠️ Algo salió mal — intentá de nuevo." if lang == "es" else "⚠️ Something went wrong — try again in a moment."
        try:
            await update.message.reply_text(err)
        except Exception:
            pass


# ── /join — нативное приглашение в канал (рычаг №2) ───────────────────────────

async def cmd_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u    = get_user(user.id)
    lang = u.get("lang", _detect_lang(user.language_code))
    await send_channel_join(context.bot, update.effective_chat.id, lang)


# ── Inline-кнопки (верификация подписки «✅ Я подписался») ─────────────────────

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    user = update.effective_user
    u    = get_user(user.id)
    lang = u.get("lang", _detect_lang(user.language_code))
    try:
        await query.answer()
    except Exception:
        pass
    data = query.data or ""
    if data == JOIN_CHECK_CB:
        try:
            await handle_join_check(context.bot, user.id, update.effective_chat.id, lang)
        except Exception as e:
            logger.error(f"join_check crashed user={user.id}: {e}", exc_info=True)
    elif data.startswith(NEWS_CB_PREFIX):
        try:
            await handle_news_callback(context.bot, user.id, update.effective_chat.id, lang, data)
        except Exception as e:
            logger.error(f"news_callback crashed user={user.id}: {e}", exc_info=True)


# ── Admin: /funnel — счётчики воронки + конверсии ─────────────────────────────

async def cmd_funnel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in _admin_ids():
        return
    snap = analytics.snapshot()
    f, r = snap["funnel"], snap["rates"]
    lines = ["📊 *Funnel*", ""]
    for k in ("cta_view", "cta_tap", "channel_open", "membership_check", "join_confirmed"):
        lines.append(f"{k}: {f.get(k, 0)}")
    lines.append("")
    lines.append(f"unique joins: {snap['unique_joins']}")
    def _r(v): return f"{v}%" if v is not None else "—"
    lines.append(f"tap/view: {_r(r['tap_per_view'])}")
    lines.append(f"join/tap: {_r(r['join_per_tap'])}")
    lines.append(f"join/view: {_r(r['join_per_view'])}")
    if snap["extra"]:
        lines.append("")
        lines.append("extra:")
        for k, v in snap["extra"].items():
            lines.append(f"  {k}: {v}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Post-init ─────────────────────────────────────────────────────────────────

async def post_init(application: Application):
    # Register commands visible in Telegram's "/" menu
    from telegram import BotCommand
    await application.bot.set_my_commands([
        BotCommand("start",  "Start / reset"),
        BotCommand("news",   "Latest news feed"),
        BotCommand("live",   "Live scores"),
        BotCommand("today",  "Upcoming matches"),
        BotCommand("policy", "Privacy policy"),
        BotCommand("lang",   "Language: en / ru / es"),
    ])
    logger.info(f"{BRAND.display_name} bot started")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("news",    cmd_news))
    app.add_handler(CommandHandler("live",    cmd_live))
    app.add_handler(CommandHandler("today",   cmd_today))
    app.add_handler(CommandHandler("policy",  cmd_policy))
    app.add_handler(CommandHandler("lang",    cmd_lang))
    app.add_handler(CommandHandler("join",    cmd_join))
    app.add_handler(CommandHandler("funnel",  cmd_funnel))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info(f"Starting {BOT_USERNAME}...")

    async def _error_handler(update, context):
        from telegram.error import Conflict, NetworkError
        if isinstance(context.error, (Conflict, NetworkError)):
            logger.warning(f"Recoverable error: {context.error}")
            return
        logger.exception(context.error)

    app.add_error_handler(_error_handler)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
