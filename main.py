import asyncio
import logging
import os
import json
import random
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Render এক্সটার্নাল URL স্বয়ংক্রিয়ভাবে নেওয়া
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://telegram-bot-1-f76m.onrender.com")

# Monetag SDK সহ মিনি অ্যাপ HTML পেজ (নরমাল অ্যাড - ২ টাকা, আনলিমিটেড)
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monetag Normal Ads</title>
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
    <div id="adblock-warning" class="warning">⚠️ সতর্কতা: অ্যাডব্লকার বন্ধ করুন!</div>
    <h1>📱 নরমাল অ্যাড জোন</h1>
    <div class="card">
        <p>ব্যালেন্স: <b id="balance" style="color: #4ade80; font-size: 20px;">৳ 0.00</b></p>
        <p>প্রতি নরমাল অ্যাড: <b>৳ ২.০০ (আনলিমিটেড)</b></p>
        <button class="btn" onclick="watchAd()">👀 অ্যাড দেখুন (+৳২)</button>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || '0';

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
                            alert('🎉 অভিনন্দন! ২ টাকা যোগ হয়েছে।');
                            document.getElementById('balance').innerText = '৳ ' + data.balance.toFixed(2);
                        }).catch(err => {
                            alert('সারਵারে আপডেট করতে সমস্যা হয়েছে।');
                        });
                }).catch((e) => {
                    alert('সম্পূর্ণ অ্যাড দেখুন।');
                });
            } else {
                alert('⚠️ অ্যাডব্লকার ডিটেক্ট করা হয়েছে!');
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

API_TOKEN = '9042324215:AAFxdjD5S6I2AKWiHj079mjSh7jDcVlp0Zg'

ADS_LINKS = [
    'https://auctionr.org/4/86bc9dc9e2d69c8dd9963e4a821caa82',
    'https://auctionr.org/4/38255cb1ee151abac58795365b4e08cf',
    'https://uplcm.com/4/10979267',
    'https://uplcm.com/4/8211939',
    'https://uplcm.com/4/12057881'
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_balances = {}
user_referrals = {}
referred_users = set()
direct_ad_counts = {}
user_last_date = {}

def check_and_reset_limit(user_id):
    today = datetime.now().date().isoformat()
    if user_last_date.get(user_id) != today:
        user_last_date[user_id] = today
        direct_ad_counts[user_id] = 0

@dp.message(Command("start"))
async def send_welcome(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    check_and_reset_limit(user_id)
    if user_id not in user_balances:
        user_balances[user_id] = 0.00
    if user_id not in user_referrals:
        user_referrals[user_id] = 0

    args = command.args
    if args and args.startswith("REF_"):
        try:
            inviter_id = int(args.split("_")[1])
            if inviter_id != user_id and (inviter_id, user_id) not in referred_users:
                referred_users.add((inviter_id, user_id))
                user_referrals[inviter_id] = user_referrals.get(inviter_id, 0) + 1
                try:
                    await bot.send_message(inviter_id, "🎉 অভিনন্দন! আপনার রেফারেলে নতুন ইউজার যুক্ত হয়েছে।")
                except:
                    pass
        except:
            pass

    web_app_url = f"{RENDER_URL}?user_id={user_id}"
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    watched_direct = direct_ad_counts.get(user_id, 0)
    remaining_direct = 10 - watched_direct

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 নরমাল অ্যাড দেখুন (৳২ - আনলিমিটেড)", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text=f"🌐 ডাইরেক্ট লিংক অ্যাড (৳৫) [{remaining_direct}/10]", callback_data="watch_direct_ad")],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet"),
         InlineKeyboardButton(text="👥 রেফারেল লিংক", callback_data="referral_info")],
        [InlineKeyboardButton(text="💸 বিকাশ উইথড্র", callback_data="withdraw_bkash")]
    ])
    
    welcome_text = (
        f"🌟 **স্বাগতম {message.from_user.first_name}!**\n\n"
        f"💰 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"🎯 আজকের বাকি ডাইরেক্ট অ্যাড: **{remaining_direct}/10 টি (৳৫ করে)**\n"
        f"📱 নরমাল অ্যাড: **৳ ২.০০ (আনলিমিটেড)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **১১২০ টাকা (বিকাশ)**\n"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "watch_direct_ad")
async def watch_direct_ad(call: types.CallbackQuery):
    user_id = call.from_user.id
    check_and_reset_limit(user_id)
    
    watched = direct_ad_counts.get(user_id, 0)
    if watched >= 10:
        await call.answer("❌ আজকের ১০টি ডাইরেক্ট অ্যাড দেখার লিমিট শেষ!", show_alert=True)
        return

    ad_url = random.choice(ADS_LINKS)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 লিংকে গিয়ে অ্যাড দেখুন", url=ad_url)],
        [InlineKeyboardButton(text="✅ অ্যাড দেখে ৫ টাকা নিন", callback_data="claim_direct_reward")],
        [InlineKeyboardButton(text="🔙 মূল মেনু", callback_data="back_home")]
    ])
    
    await call.message.edit_text(
        f"🌐 **ডাইরেক্ট লিংক অ্যাড (৫ টাকা)**\n\n"
        f"১. নিচের লিংকে ক্লিক করে ভিজিট করুন।\n"
        f"২. ফিরে এসে নিচে বাটনে ক্লিক করে ৫ টাকা নিন।\n\n"
        f"আজ দেখা হয়েছে: {watched}/10 টি",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "claim_direct_reward")
async def claim_direct_reward(call: types.CallbackQuery):
    user_id = call.from_user.id
    check_and_reset_limit(user_id)
    
    watched = direct_ad_counts.get(user_id, 0)
    if watched >= 10:
        await call.answer("❌ লিমিট শেষ!", show_alert=True)
        return
        
    direct_ad_counts[user_id] = watched + 1
    user_balances[user_id] = user_balances.get(user_id, 0.00) + 5.00
    
    remaining = 10 - direct_ad_counts[user_id]
    balance = user_balances[user_id]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 আরেকটি ডাইরেক্ট অ্যাড দেখুন", callback_data="watch_direct_ad")],
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    await call.answer("🎉 সফল! ৫ টাকা যোগ হয়েছে।", show_alert=True)
    await call.message.edit_text(
        f"✅ **সফলভাবে ৫ টাকা যোগ হয়েছে!**\n\n"
        f"💰 ব্যালেন্স: ৳ {balance:.2f}\n"
        f"📊 আজকের বাকি ডাইরেক্ট অ্যাড: {remaining}/10 টি",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "wallet")
async def check_wallet(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    await call.answer(f"💰 ব্যালেন্স: ৳ {balance:.2f} | রেফার: {refs}/7 টি\nন্যূনতম বিকাশ উইথড্র: ৳ 1120.00", show_alert=True)

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
        "💡 উইথড্র করতে কমপক্ষে ৭টি সফল রেফার লাগবে!"
    )
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(lambda c: c.data == "withdraw_bkash")
async def withdraw_bkash(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    
    if balance < 1120.00 or refs < 7:
        needed_bal = max(0, 1120.00 - balance)
        needed_refs = max(0, 7 - refs)
        msg = "❌ বিকাশ উইথড্র শর্ত পূর্ণ হয়নি!\n"
        if balance < 1120.00:
            msg += f"- আরও ৳ {needed_bal:.2f} প্রয়োজন\n"
        if refs < 7:
            msg += f"- আরও {needed_refs}টি রেফার প্রয়োজন\n"
        await call.answer(msg, show_alert=True)
    else:
        await call.answer("✅ আপনার বিকাশ উইথড্র রিকোয়েস্ট সফল হয়েছে! অ্যাডমিন যাচাই করে পেমেন্ট পাঠিয়ে দেবেন।", show_alert=True)

@dp.callback_query(lambda c: c.data == "back_home")
async def back_home(call: types.CallbackQuery):
    user_id = call.from_user.id
    check_and_reset_limit(user_id)
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    web_app_url = f"{RENDER_URL}?user_id={user_id}"
    watched_direct = direct_ad_counts.get(user_id, 0)
    remaining_direct = 10 - watched_direct

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 নরমাল অ্যাড দেখুন (৳২ - আনলিমিটেড)", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text=f"🌐 ডাইরেক্ট লিংক অ্যাড (৳৫) [{remaining_direct}/10]", callback_data="watch_direct_ad")],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet"),
         InlineKeyboardButton(text="👥 রেফারেল লিংক", callback_data="referral_info")],
        [InlineKeyboardButton(text="💸 বিকাশ উইথড্র", callback_data="withdraw_bkash")]
    ])
    
    welcome_text = (
        f"🌟 **স্বাগতম!**\n\n"
        f"💰 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"🎯 আজকের বাকি ডাইরেক্ট অ্যাড: **{remaining_direct}/10 টি (৳৫ করে)**\n"
        f"📱 নরমাল অ্যাড: **৳ ২.০০ (আনলিমিটেড)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **১১২০ টাকা (বিকাশ)**\n"
    )
    
    await call.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
