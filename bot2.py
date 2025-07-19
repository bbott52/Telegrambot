import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import sqlite3
import threading
import time
import random
import requests
import undetected_chromedriver.v2 as uc
from selenium.webdriver.chrome.options import Options

=== CONFIG ===

BOT_TOKEN = "7854510116:AAEpFEs3b_YVNs4jvFH6d1JOZ5Dern69_Sg"
bot = telebot.TeleBot(BOT_TOKEN)
admin_id = 6976365864
user_tasks = {}

=== DATABASE SETUP ===

conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY,
telegram_id TEXT UNIQUE,
username TEXT,
is_premium INTEGER DEFAULT 0,
referrals INTEGER DEFAULT 0,
premium_expiry TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS links (
id INTEGER PRIMARY KEY,
telegram_id TEXT,
url TEXT,
interval INTEGER,
added_at TEXT,
expires_at TEXT,
active INTEGER DEFAULT 1
)
''')
conn.commit()

=== UTILS ===

user_agents = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
"Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)",
"Mozilla/5.0 (Linux; Android 11; SM-G991B)",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

def fake_visit(url, interval):
def visit_loop():
while True:
headers = {"User-Agent": random.choice(user_agents)}
try:
response = requests.get(url, headers=headers, timeout=5)
print(f"[✓] Visited: {url} - Status {response.status_code}")
except Exception as e:
print(f"[!] Error visiting {url}: {e}")
time.sleep(interval)
thread = threading.Thread(target=visit_loop)
thread.daemon = True
thread.start()

def browser_visit_youtube(url, interval):
def visit_loop():
while True:
try:
print(f"[...] Opening browser for {url}")
options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = uc.Chrome(options=options)  
            driver.get(url)  
            print(f"[✓] Watching: {url}")  
            time.sleep(random.randint(35, 60))  # stay at least 30s  
            driver.quit()  
        except Exception as e:  
            print(f"[!] Browser error: {e}")  
            try:  
                driver.quit()  
            except:  
                pass  
        time.sleep(interval)  

thread = threading.Thread(target=visit_loop)  
thread.daemon = True  
thread.start()

=== DATABASE FUNCTIONS ===

def add_user(telegram_id, username):
cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
conn.commit()

def get_user(telegram_id):
cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
return cursor.fetchone()

def update_referral(telegram_id):
cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE telegram_id = ?", (telegram_id,))
conn.commit()

def set_premium(telegram_id, months):
expiry = (datetime.now() + timedelta(days=30 * months)).isoformat()
cursor.execute("UPDATE users SET is_premium = 1, premium_expiry = ? WHERE telegram_id = ?", (expiry, telegram_id))
conn.commit()

def add_link(telegram_id, url, interval, duration_days):
now = datetime.now()
expires = now + timedelta(days=duration_days)
cursor.execute("INSERT INTO links (telegram_id, url, interval, added_at, expires_at) VALUES (?, ?, ?, ?, ?)",
(telegram_id, url, interval, now.isoformat(), expires.isoformat()))
conn.commit()

def get_links_by_user(telegram_id):
cursor.execute("SELECT * FROM links WHERE telegram_id = ? AND active = 1", (telegram_id,))
return cursor.fetchall()

def stop_link(link_id):
cursor.execute("UPDATE links SET active = 0 WHERE id = ?", (link_id,))
conn.commit()

def delete_expired_links():
now = datetime.now().isoformat()
cursor.execute("UPDATE links SET active = 0 WHERE expires_at < ?", (now,))
conn.commit()

=== START COMMAND ===

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

=== ADD LINK ===

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
msg = bot.reply_to(message, "⏱ Interval in seconds (10–60):")
bot.register_next_step_handler(msg, lambda m: save_link(m, url))

def save_link(message, url):
try:
interval = int(message.text.strip())
if not 10 <= interval <= 60:
raise ValueError
except:
bot.reply_to(message, "❌ Invalid number. Try again.")
return

telegram_id = str(message.from_user.id)  
user = get_user(telegram_id)  
duration = 1 if user[4] >= 3 else 3 if user[3] == 0 else 90  
add_link(telegram_id, url, interval, duration)  

# YouTube detection  
if "youtube.com" in url or "youtu.be" in url:  
    browser_visit_youtube(url, interval)  
else:  
    fake_visit(url, interval)  

bot.send_message(message.chat.id, f"✅ Your link is now being visited every {interval} seconds.")

=== MY LINK ===

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

=== PREMIUM ===

@bot.message_handler(func=lambda m: m.text == "💎 Buy Premium")
def buy_premium(message):
bot.send_message(message.chat.id, (
"💎 Buy Premium Access\n\n"
"• $5 → 3 months\n• $10 → 6 months\n• $20 → 1 year\n• $50 → Lifetime\n\n"
"Send BNB/USDT (BEP20) to:\n0xa84bd2cfbBad66Ae2c5daf9aCe764dc845b94C7C\n\n"
"Then send proof to Admin ⬇️"
), parse_mode="Markdown")
markup = InlineKeyboardMarkup()
markup.add(InlineKeyboardButton("📤 Send Proof to Admin", url="https://wa.me/2349114301708"))
bot.send_message(message.chat.id, "⬇️ Click below to submit proof", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👥 Referrals")
def referral_handler(message):
telegram_id = str(message.from_user.id)
link = f"https://t.me/boostlinkbot?start={telegram_id}"
user = get_user(telegram_id)
referred = user[4]
bot.send_message(message.chat.id, f"👥 You’ve referred {referred}/3 users.\n\nYour link:\n{link}")

@bot.message_handler(func=lambda m: m.text == "🆘 Help")
def help_handler(message):
bot.send_message(message.chat.id, (
"📖 Bot Guide\n\n"
"• Free users: 1 link for 3 days\n"
"• Referrals: 3 users = +1 day\n"
"• Premium = Unlimited links\n"
"• Use /start if stuck"
), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📞 Admin Contact")
def contact_admin(message):
markup = InlineKeyboardMarkup()
markup.add(InlineKeyboardButton("📞 Message Admin", url="https://wa.me/2349114301708"))
bot.send_message(message.chat.id, "Need help? Contact admin below:", reply_markup=markup)

=== CLEANUP ===

def cleanup_task():
while True:
delete_expired_links()
time.sleep(3600)

threading.Thread(target=cleanup_task, daemon=True).start()

=== RUN ===

print("✅ Bot is running...")
bot.infinity_polling()

