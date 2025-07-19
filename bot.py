import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import *
from utils import fake_visit, delete_expired_links

BOT_TOKEN = "7854510116:AAEpFEs3b_YVNs4jvFH6d1JOZ5Dern69_Sg"
bot = telebot.TeleBot(BOT_TOKEN)

admin_id = 6976365864

# Track task completion per user (start screen)
user_tasks = {}

@bot.message_handler(commands=["start"])
def start(message):
    telegram_id = str(message.from_user.id)
    username = message.from_user.username or "None"
    add_user(telegram_id, username)

    if telegram_id not in user_tasks:
        user_tasks[telegram_id] = True
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Subscribed", callback_data="done_task"))
        msg = (
            "👋 *Welcome!*\n\n"
            "✅ Before using the bot, please:\n"
            "1. Subscribe to our [YouTube](https://youtube.com/@bbottecbot?si=t0aOppFrAyOFkB_E)\n"
            "2. Join our [Telegram Channel](https://t.me/boostlinkv)\n\n"
            "Once done, tap the button below."
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)
    else:
        show_main_menu(message)

@bot.callback_query_handler(func=lambda c: c.data == "done_task")
def confirm_task(callback_query):
    telegram_id = str(callback_query.from_user.id)
    user_tasks.pop(telegram_id, None)
    bot.answer_callback_query(callback_query.id, "✅ Task confirmed.")
    show_main_menu(callback_query.message)

def show_main_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Add Link", "📋 My Link")
    markup.row("👥 Referrals", "💎 Buy Premium")
    markup.row("🆘 Help", "📞 Admin Contact")
    bot.send_message(message.chat.id, "👇 Main Menu", reply_markup=markup)

# ➕ ADD LINK
@bot.message_handler(func=lambda m: m.text == "➕ Add Link")
def add_link_start(message):
    telegram_id = str(message.from_user.id)
    links = get_links_by_user(telegram_id)
    user = get_user(telegram_id)
    if user[3] == 0 and len(links) >= 1 and user[4] < 3:
        bot.reply_to(message, "🚫 Free users can only add 1 link.\nRefer 3 users or go premium.")
        return

    msg = bot.reply_to(message, "🔗 Send the link to boost:")
    bot.register_next_step_handler(msg, ask_time)

def ask_time(message):
    url = message.text.strip()
    msg = bot.reply_to(message, "⏱ Interval in seconds (1–60):")
    bot.register_next_step_handler(msg, lambda m: save_link(m, url))

def save_link(message, url):
    try:
        interval = int(message.text.strip())
        if not 1 <= interval <= 60:
            raise ValueError
    except:
        bot.reply_to(message, "❌ Invalid number. Try again.")
        return

    telegram_id = str(message.from_user.id)
    user = get_user(telegram_id)
    duration = 1 if user[4] >= 3 else 3 if user[3] == 0 else 90
    add_link(telegram_id, url, interval, duration)
    fake_visit(url, interval)
    bot.send_message(message.chat.id, f"✅ Your link is now being visited every {interval} seconds.")

# 📋 MY LINK
@bot.message_handler(func=lambda m: m.text == "📋 My Link")
def my_links(message):
    telegram_id = str(message.from_user.id)
    links = get_links_by_user(telegram_id)
    if not links:
        bot.reply_to(message, "⛔ You have no active links.")
        return

    for link in links:
        bot.send_message(
            message.chat.id,
            f"🔗 {link[2]}\n⏱ Every {link[3]}s\n🗓 Expires: {link[5][:10]}",
        )

# 💎 BUY PREMIUM
@bot.message_handler(func=lambda m: m.text == "💎 Buy Premium")
def buy_premium(message):
    bot.send_message(message.chat.id, (
        "💎 *Buy Premium Access*\n\n"
        "🔓 Premium Plans:\n"
        "• $5 → 3 months\n"
        "• $10 → 6 months\n"
        "• $20 → 1 year\n"
        "• $50 → Lifetime access\n\n"
        "📩 Pay with BNB or USDT (BEP20) to:\n"
        "`0xa84bd2cfbBad66Ae2c5daf9aCe764dc845b94C7C`\n\n"
        "⚠️ After payment, send *screenshot & TX hash* to Admin below ⬇️",
    ), parse_mode="Markdown")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 Send Proof to Admin", url="https://wa.me/2349114301708?text=Hi!%20From%20your%20bot%20on%20Telegram"))
    bot.send_message(message.chat.id, "⬇️ Click below to submit proof", reply_markup=markup)

# 👥 REFERRALS (basic template)
@bot.message_handler(func=lambda m: m.text == "👥 Referrals")
def referral_handler(message):
    telegram_id = str(message.from_user.id)
    link = f"https://t.me/boostlinkbot?start={telegram_id}"
    user = get_user(telegram_id)
    referred = user[4]
    bot.send_message(message.chat.id, f"👥 You’ve referred {referred}/3 users.\n\nShare your link:\n{link}")

# 🆘 HELP
@bot.message_handler(func=lambda m: m.text == "🆘 Help")
def help_handler(message):
    bot.send_message(message.chat.id, (
        "📖 *Bot Guide*\n\n"
        "• Add Link: Submit any link to get auto-visited\n"
        "• Free users: 1 link for 3 days\n"
        "• Referrals: Invite 3 friends = 1 link for 1 day\n"
        "• Premium: Add unlimited links, longer durations\n"
        "• Contact Admin if stuck\n"
    ), parse_mode="Markdown")

# 📞 ADMIN CONTACT
@bot.message_handler(func=lambda m: m.text == "📞 Admin Contact")
def contact_admin(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Message Admin on WhatsApp", url="https://wa.me/2349114301708?text=Hi!%20From%20your%20bot%20on%20Telegram"))
    bot.send_message(message.chat.id, "Need help? Contact admin below:", reply_markup=markup)

# ⏰ Delete expired links every few hours
import threading, time
def cleanup_task():
    while True:
        delete_expired_links()
        time.sleep(3600)

threading.Thread(target=cleanup_task, daemon=True).start()

# Start bot
print("✅ Bot is running...")
bot.infinity_polling()