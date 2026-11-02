import asyncio
import logging
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# আপনার Render Web Service-এর লাইভ লিংক এখানে দিন
RENDER_URL = os.environ.get("RENDER_URL", "https://telegram-bot-1-f76m.onrender.com")

# Monetag SDK সহ মিনি অ্যাপ HTML পেজ
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monetag Rewarded PTC</title>
    <!-- Monetag SDK -->
    <script src='//libtl.com/sdk.js' data-zone='12176564' data-sdk='show_12176564'></script>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #0f172a; color: #fff; padding: 20px; margin: 0; }
        .btn { background: #3b82f6; color: white; border: none; padding: 14px 24px; font-size: 16px; border-radius: 10px; cursor: pointer; margin-top: 15px; text-decoration: none; display: inline-block; font-weight: bold; box-shadow: 0 4px 10px rgba(59,130,246,0.4); width: 85%; max-width: 320px; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        h1 { color: #38bdf8; font-size: 22px; }
        .warning { background: #ef4444; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; display: none; font-size: 14px; font-weight: bold; }
    </style>
</head>
<body>
    <div id="adblock-warning" class="warning">⚠️ সতর্কতা: আপনার ব্রাউজারে Adblocker সক্রিয় রয়েছে! রিওয়ার্ড পেতে অ্যাডব্লকার বন্ধ করুন।</div>
    <h1>🎯 Monetag Rewarded Ads</h1>
    <div class="card">
        <p>বর্তমান ব্যালেন্স: <b id="balance" style="color: #4ade80; font-size: 20px;">৳ 0.00</b></p>
        <p>প্রতি অ্যাড ভিউ: <b>৳ ২.০০</b></p>
        <p style="color: #cbd5e1; font-size: 14px;">যত খুশি তত অ্যাড দেখে ইনকাম করুন!</p>
        <button class="btn" onclick="watchAd()">👀 অ্যাড দেখুন (৳২ নিন)</button>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || '0';

        // Check Adblocker
        setTimeout(() => {
            if (typeof show_12176564 === 'undefined') {
                document.getElementById('adblock-warning').style.display = 'block';
            }
        }, 1000);

        function watchAd() {
            if (typeof show_12176564 === 'function') {
                show_12176564().then(() => {
                    fetch('/reward?user_id=' + userId)
                        .then(res => res.json())
                        .then(data => {
                            alert('🎉 অভিনন্দন! সফলভাবে অ্যাড দেখেছেন এবং ২ টাকা যোগ হয়েছে।');
                            document.getElementById('balance').innerText = '৳ ' + data.balance.toFixed(2);
                        }).catch(err => {
                            alert('ব্যালেন্স আপডেট করতে সমস্যা হয়েছে।');
                        });
                }).catch((e) => {
                    alert('অ্যাড লোড হয়নি বা স্কিপ করা হয়েছে। সম্পূর্ণ অ্যাড দেখুন।');
                });
            } else {
                alert('⚠️ Adblocker ডিটেক্ট করা হয়েছে! দয়া করে অ্যাডব্লকার বন্ধ করে আবার চেষ্টা করুন।');
            }
        }
    </script>
</body>
</html>
"""

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/reward':
            user_id = int(query_params.get('user_id', ['0'])[0])
            if user_id > 0:
                current = user_balances.get(user_id, 0.00)
                user_balances[user_id] = current + 2.00
                new_bal = user_balances[user_id]
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "balance": new_bal}).encode('utf-8'))
                return

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(MINI_APP_HTML.encode('utf-8'))

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# আপনার বটের টোকেন
API_TOKEN = '9042324215:AAFxdjD5S6I2AKWiHj079mjSh7jDcVlp0Zg'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ডাটাবেস ডিকশনারি
user_balances = {}
user_referrals = {}
referred_users = set()

@dp.message(Command("start"))
async def send_welcome(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.00
    if user_id not in user_referrals:
        user_referrals[user_id] = 0

    # রেফারেল হ্যান্ডলিং
    args = command.args
    if args and args.startswith("REF_"):
        try:
            inviter_id = int(args.split("_")[1])
            if inviter_id != user_id and (inviter_id, user_id) not in referred_users:
                referred_users.add((inviter_id, user_id))
                user_referrals[inviter_id] = user_referrals.get(inviter_id, 0) + 1
                try:
                    await bot.send_message(inviter_id, "🎉 অভিনন্দন! আপনার রেফারেলে একজন নতুন ব্যবহারকারী যুক্ত হয়েছেন।")
                except:
                    pass
        except:
            pass

    web_app_url = f"{RENDER_URL}?user_id={user_id}"
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 মিনি অ্যাপে অ্যাড দেখুন (৳২/অ্যাড)", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet"),
         InlineKeyboardButton(text="👥 রেফারেল লিংক", callback_data="referral_info")],
        [InlineKeyboardButton(text="💸 উইথড্র করুন", callback_data="withdraw")]
    ])
    
    welcome_text = (
        f"🌟 **স্বাগতম {message.from_user.first_name}!**\n\n"
        f"💰 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"💵 প্রতি অ্যাড ভিউ: **৳ ২.০০ (আনলিমিটেড)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **১১২০ টাকা** (৭টি রেফার বাধ্যতামূলক)\n\n"
        "নিচের বাটন থেকে মিনি অ্যাপে প্রবেশ করে অ্যাড দেখা শুরু করুন!"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "wallet")
async def check_wallet(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    await call.answer(f"💰 ব্যালেন্স: ৳ {balance:.2f} | রেফার: {refs}/7 টি\nন্যূনতম উইথড্র: ৳ 1120.00", show_alert=True)

@dp.callback_query(lambda c: c.data == "referral_info")
async def referral_info(call: types.CallbackQuery):
    user_id = call.from_user.id
    refs = user_referrals.get(user_id, 0)
    ref_link = f"https://t.me/Money_Earn_2200_bot?start=REF_{user_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="back_home")]
    ])
    
    text = (
        f"👥 **রেফারেল প্রোগ্রাম**\n\n"
        f"আপনার রেফার লিংক:\n`{ref_link}`\n\n"
        f"📊 আপনার মোট রেফার: **{refs} / 7 টি**\n\n"
        "💡 উইথড্র করার জন্য কমপক্ষে ৭টি সফল রেফার করতে হবে!"
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(lambda c: c.data == "withdraw")
async def withdraw_request(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    
    if balance < 1120.00 or refs < 7:
        needed_bal = max(0, 1120.00 - balance)
        needed_refs = max(0, 7 - refs)
        msg = "❌ উইথড্র শর্ত পূর্ণ হয়নি!\n"
        if balance < 1120.00:
            msg += f"- আরও ৳ {needed_bal:.2f} প্রয়োজন\n"
        if refs < 7:
            msg += f"- আরও {needed_refs}টি রেফার প্রয়োজন\n"
        await call.answer(msg, show_alert=True)
    else:
        await call.answer("✅ উইথড্র রিকোয়েস্ট সফলভাবে সাবমিট হয়েছে! অ্যাডমিন চেক করে পেমেন্ট পাঠিয়ে দেবেন।", show_alert=True)

@dp.callback_query(lambda c: c.data == "back_home")
async def back_home(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    web_app_url = f"{RENDER_URL}?user_id={user_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 মিনি অ্যাপে অ্যাড দেখলে ইনকাম করুন", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet"),
         InlineKeyboardButton(text="👥 রেফারেল লিংক", callback_data="referral_info")],
        [InlineKeyboardButton(text="💸 উইথড্র করুন", callback_data="withdraw")]
    ])
    
    welcome_text = (
        f"🌟 **স্বাগতম!**\n\n"
        f"💰 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"💵 প্রতি অ্যাড ভিউ: **৳ ২.০০ (আনলিমিটেড)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **১১২০ টাকা** (৭টি রেফার বাধ্যতামূলক)\n\n"
        "নিচের বাটন থেকে মিনি অ্যাপে প্রবেশ করে অ্যাড দেখা শুরু করুন!"
    )
    
    await call.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
