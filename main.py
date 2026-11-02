import asyncio
import logging
import os
import json
import random
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://telegram-bot-1-f76m.onrender.com")

MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Earning Mini App</title>
    <!-- Monetag SDK -->
    <script src='//libtl.com/sdk.js' data-zone='12176564' data-sdk='show_12176564'></script>
    <!-- Adsterra Native Ad Script -->
    <script async="async" data-cfasync="false" src="https://biomanos.org/21/fdd24f280dc0789b50029181f039ea62"></script>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #0f172a; color: #fff; padding: 15px; margin: 0; }
        .btn { background: #3b82f6; color: white; border: none; padding: 12px 20px; font-size: 15px; border-radius: 10px; cursor: pointer; margin-top: 10px; text-decoration: none; display: inline-block; font-weight: bold; box-shadow: 0 4px 10px rgba(59,130,246,0.4); width: 85%; max-width: 320px; }
        .btn-adsterra { background: #10b981; }
        .card { background: #1e293b; padding: 20px; border-radius: 16px; margin-top: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        h1 { color: #38bdf8; font-size: 20px; }
        .warning { background: #ef4444; color: white; padding: 10px; border-radius: 8px; margin-bottom: 10px; display: none; font-size: 13px; font-weight: bold; }
        .native-ad-box { background: #334155; padding: 15px; border-radius: 12px; margin-top: 15px; }
    </style>
</head>
<body>
    <div id="adblock-warning" class="warning">⚠️ সতর্কতা: অ্যাডব্লকার বন্ধ করুন!</div>
    <h1>📱 আলাদা অ্যাড আর্নিং জোন</h1>
    
    <!-- Monetag Section -->
    <div class="card">
        <h3 style="color: #38bdf8; margin-top: 0;">🎯 Monetag Rewarded Ads</h3>
        <p>রেট: <b>৳ ১.৫০</b> | লিমিট: <b>৩০টি/দিন</b></p>
        <button class="btn" onclick="watchMonetagAd()">👀 Monetag অ্যাড দেখুন</button>
    </div>

    <!-- Adsterra Native Section -->
    <div class="card">
        <h3 style="color: #34d399; margin-top: 0;">💎 Adsterra Native Ads</h3>
        <p>রেট: <b>৳ ১.৫০</b> | লিমিট: <b>১৫টি/দিন (নিরাপদ)</b></p>
        <div class="native-ad-box">
            <div id="container-fdd24f280dc0789b50029181f039ea62"></div>
        </div>
        <button class="btn btn-adsterra" onclick="claimAdsterraReward()">✅ Adsterra রিওয়ার্ড নিন</button>
    </div>

    <p style="margin-top: 20px; color: #4ade80; font-size: 18px;">টোটাল ব্যালেন্স: <b id="balance">৳ 0.00</b></p>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || '0';

        setTimeout(() => {
            if (typeof show_12176564 === 'undefined') {
                document.getElementById('adblock-warning').style.display = 'block';
            }
        }, 1000);

        function watchMonetagAd() {
            if (typeof show_12176564 === 'function') {
                show_12176564().then(() => {
                    fetch('/reward?type=monetag&user_id=' + userId)
                        .then(res => res.json())
                        .then(data => {
                            if(data.status === 'success') {
                                alert('🎉 অভিনন্দন! Monetag থেকে ১.৫০ টাকা যোগ হয়েছে।');
                                document.getElementById('balance').innerText = '৳ ' + data.balance.toFixed(2);
                            } else {
                                alert(data.message);
                            }
                        }).catch(err => {
                            alert('সার্ভারে আপডেট করতে সমস্যা হয়েছে।');
                        });
                }).catch((e) => {
                    alert('সম্পূর্ণ অ্যাড দেখুন।');
                });
            } else {
                alert('⚠️ অ্যাডব্লকার ডিটেক্ট করা হয়েছে!');
            }
        }

        function claimAdsterraReward() {
            fetch('/reward?type=adsterra&user_id=' + userId)
                .then(res => res.json())
                .then(data => {
                    if(data.status === 'success') {
                        alert('🎉 অভিনন্দন! Adsterra নেটিভ অ্যাড থেকে ১.৫০ টাকা যোগ হয়েছে।');
                        document.getElementById('balance').innerText = '৳ ' + data.balance.toFixed(2);
                    } else {
                        alert(data.message);
                    }
                }).catch(err => {
                    alert('সার্ভারে আপডেট করতে সমস্যা হয়েছে।');
                });
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
            ad_type = query_params.get('type', [''])[0]
            user_id = int(query_params.get('user_id', ['0'])[0])
            
            if user_id > 0:
                today = datetime.now().date().isoformat()
                
                if ad_type == 'monetag':
                    if user_monetag_dates.get(user_id) != today:
                        user_monetag_dates[user_id] = today
                        user_monetag_counts[user_id] = 0
                    
                    if user_monetag_counts.get(user_id, 0) >= 30:
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "limit", "message": "আজকের Monetag ৩০টি অ্যাড দেখার লিমিট শেষ!"}).encode('utf-8'))
                        return
                    
                    user_monetag_counts[user_id] = user_monetag_counts.get(user_id, 0) + 1

                elif ad_type == 'adsterra':
                    if user_adsterra_dates.get(user_id) != today:
                        user_adsterra_dates[user_id] = today
                        user_adsterra_counts[user_id] = 0
                    
                    if user_adsterra_counts.get(user_id, 0) >= 15:
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "limit", "message": "আজকের Adsterra নিরাপদ ১৫টি অ্যাড দেখার লিমিট শেষ!"}).encode('utf-8'))
                        return
                    
                    user_adsterra_counts[user_id] = user_adsterra_counts.get(user_id, 0) + 1

                current = user_balances.get(user_id, 0.00)
                user_balances[user_id] = current + 1.50
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
ADMIN_USERNAME = "@Cutemaliha"

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

all_users = set()
user_balances = {}
user_referrals = {}
referred_users = set()
direct_ad_counts = {}
user_monetag_counts = {}
user_adsterra_counts = {}
user_last_date = {}
user_monetag_dates = {}
user_adsterra_dates = {}
ad_click_time = {}

PAYMENT_GROUP_URL = "https://t.me/+UnjopXEVXEY3NTJl"

def check_and_reset_limit(user_id):
    today = datetime.now().date().isoformat()
    if user_last_date.get(user_id) != today:
        user_last_date[user_id] = today
        direct_ad_counts[user_id] = 0

@dp.message(Command("start"))
async def send_welcome(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    all_users.add(user_id)
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
        [InlineKeyboardButton(text="📢 পেমেন্ট গ্রুপে জয়েন করুন (বাধ্যতামূলক)", url=PAYMENT_GROUP_URL)],
        [InlineKeyboardButton(text="📱 মিনি অ্যাপে (Monetag & Adsterra) কাজ করুন", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text=f"🌐 ডাইরেক্ট লিংক অ্যাড (৳৫) [{remaining_direct}/10]", callback_data="watch_direct_ad")],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet"),
         InlineKeyboardButton(text="👥 রেফারেল লিংক", callback_data="referral_info")],
        [InlineKeyboardButton(text="💸 বিকাশ উইথড্র", callback_data="withdraw_bkash")]
    ])
    
    welcome_text = (
        f"🌟 **স্বাগতম {message.from_user.first_name}!**\n\n"
        "⚠️ **সতর্কতা ও ঘোষণা:**\n"
        "অবাস্তব ইনকাম দেখে প্রতারিত হবেন না। আমরা সবসময় যেইটা আপনাদের দেওয়া সম্ভব সেইটাই দিয়ে থাকি। মন দিয়ে কাজ করুন। সবাই পেমেন্ট পাবেন। \n"
        "📅 **পেমেন্ট শিডিউল:** প্রতি মাসের ১৭-১৯ তারিখ এবং ১-৩ তারিখ সকল পয়েন্ট পেমেন্ট করা হয়।\n\n"
        f"💰 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"🎯 ডাইরেক্ট লিংক অ্যাড: **৳ ৫.০০ (বাকি {remaining_direct}/10 টি)**\n"
        f"🎯 Monetag অ্যাড: **৳ ১.৫০ (সর্বোচ্চ ৩০টি/দিন)**\n"
        f"💎 Adsterra নেটিভ অ্যাড: **৳ ১.৫০ (সর্বোচ্চ ১৫টি/দিন)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **৮৫০ টাকা (বিকাশ - ৫% ফি)**\n"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("stats"))
async def bot_stats(message: types.Message):
    total_active_users = len(all_users)
    await message.answer(f"📊 **বট স্ট্যাটিস্টিক্স:**\n\n👥 মোট ইউনিক ব্যবহারকারী: **{total_active_users} জন**")

@dp.callback_query(lambda c: c.data == "watch_direct_ad")
async def watch_direct_ad(call: types.CallbackQuery):
    user_id = call.from_user.id
    check_and_reset_limit(user_id)
    
    watched = direct_ad_counts.get(user_id, 0)
    if watched >= 10:
        await call.answer("❌ আজকের ১০টি ডাইরেক্ট অ্যাড দেখার লিমিট শেষ!", show_alert=True)
        return

    ad_url = random.choice(ADS_LINKS)
    ad_click_time[user_id] = time.time()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 লিংকে গিয়ে অ্যাড দেখুন", url=ad_url)],
        [InlineKeyboardButton(text="🔄 ভিজিট শেষ করে এখানে ক্লিক করুন", callback_data="verify_visit")],
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    await call.message.edit_text(
        f"🌐 **ডাইরেক্ট লিংক অ্যাড (৫ টাকা)**\n\n"
        f"১. প্রথমে **'🌐 লিংকে গিয়ে অ্যাড দেখুন'** বাটনে ক্লিক করে ওয়েবসাইট ভিজিট করুন এবং অন্তত ১২ সেকেন্ড থাকুন।\n"
        f"২. সময় শেষ হওয়ার পর **'🔄 ভিজিট শেষ করে এখানে ক্লিক করুন'** বাটনে ক্লিক করুন।\n\n"
        f"📊 আজ দেখা হয়েছে: {watched}/10 টি",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "verify_visit")
async def verify_visit(call: types.CallbackQuery):
    user_id = call.from_user.id
    last_click = ad_click_time.get(user_id, 0)
    elapsed = time.time() - last_click
    
    if elapsed < 12:
        remaining = int(12 - elapsed)
        await call.answer(f"⚠️ খুব দ্রুত ক্লিক করেছেন! লিংকে গিয়ে আরও অন্তত {remaining} সেকেন্ড অপেক্ষা করুন।", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 ৫ টাকা কালেক্ট করুন", callback_data="claim_direct_reward")],
        [InlineKeyboardButton(text="🔄 আবার ভিজিট করুন", callback_data="watch_direct_ad")],
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    await call.message.edit_text(
        "✅ আপনার ভিজিট সফলভাবে যাচাই করা হয়েছে। এখন নিচের **'🎁 ৫ টাকা কালেক্ট করুন'** বাটনে ক্লিক করুন!",
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    await call.message.edit_text(
        f"💰 **আপনার ওয়ালেট**\n\n"
        f"💵 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"👥 সফল রেফার: **{refs} / 7 টি**\n"
        f"💳 ন্যূনতম বিকাশ উইথড্র: **৳ ৮৫০.০০** (৫% ফি)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "referral_info")
async def referral_info(call: types.CallbackQuery):
    user_id = call.from_user.id
    refs = user_referrals.get(user_id, 0)
    ref_link = f"https://t.me/Money_Earn_2200_bot?start=REF_{user_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    if balance < 850.00 or refs < 7:
        needed_bal = max(0, 850.00 - balance)
        needed_refs = max(0, 7 - refs)
        msg = f"❌ **বিকাশ উইথড্র শর্ত পূর্ণ হয়নি!**\n\n"
        if balance < 850.00:
            msg += f"• আরও ব্যালেন্স প্রয়োজন: ৳ {needed_bal:.2f}\n"
        if refs < 7:
            msg += f"• আরও রেফার প্রয়োজন: {needed_refs}টি\n\n"
            msg += "শর্তগুলো পূরণ করে আবার উইথড্র করুন。"
        await call.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    else:
        extra_amount = balance - 850.00
        user_balances[user_id] = 0.00
        
        success_msg = (
            f"✅ **বিকাশ উইথড্র রিকোয়েস্ট সফল হয়েছে!**\n\n"
            f"নির্ধারিত নিয়ম অনুযায়ী ৫% ফি কেটে নেওয়া হয়েছে এবং প্রতি মাসের ১৭-১৯ তারিখ ও ১-৩ তারিখের মধ্যে পেমেন্ট সম্পন্ন করা হবে।"
        )
        if extra_amount > 0:
            success_msg += f"\n\n(উল্লেখ্য: ৮৫০ টাকার ওপরের অতিরিক্ত ৳ {extra_amount:.2f} এডমিন {ADMIN_USERNAME} এর অ্যাকাউন্টে স্থানান্তরিত হয়েছে।)"
            
        await call.message.edit_text(success_msg, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

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
        [InlineKeyboardButton(text="📢 পেমেন্ট গ্রুপে জয়েন করুন", url=PAYMENT_GROUP_URL)],
        [InlineKeyboardButton(text="📱 মিনি অ্যাপে (Monetag & Adsterra) কাজ করুন", web_app=WebAppInfo(url=web_app_url))],
        [InlineKeyboardButton(text=f"🌐 ডাইরেক্ট লিংক অ্যাড (৳৫) [{remaining_direct}/10]", callback_data="watch_direct_ad")],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet"),
         InlineKeyboardButton(text="👥 রেফারেল লিংক", callback_data="referral_info")],
        [InlineKeyboardButton(text="💸 বিকাশ উইথড্র", callback_data="withdraw_bkash")]
    ])
    
    welcome_text = (
        f"🌟 **স্বাগতম!**\n\n"
        "⚠️ **সতর্কতা ও ঘোষণা:**\n"
        "অবাস্তব ইনকাম দেখে প্রতারিত হবেন না। আমরা সবসময় যেইটা আপনাদের দেওয়া সম্ভব সেইটাই দিয়ে থাকি। মন দিয়ে কাজ করুন। সবাই পেমেন্ট পাবেন। \n"
        "📅 **পেমেন্ট শিডিউল:** প্রতি মাসের ১৭-১৯ তারিখ এবং ১-৩ তারিখ সকল পয়েন্ট পেমেন্ট করা হয়।\n\n"
        f"💰 বর্তমান ব্যালেন্স: **৳ {balance:.2f}**\n"
        f"🎯 ডাইরেক্ট লিংক অ্যাড: **৳ ৫.০০ (বাকি {remaining_direct}/10 টি)**\n"
        f"🎯 Monetag অ্যাড: **৳ ১.৫০ (সর্বোচ্চ ৩০টি/দিন)**\n"
        f"💎 Adsterra নেটিভ অ্যাড: **৳ ১.৫০ (সর্বোচ্চ ১৫টি/দিন)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **৮৫০ টাকা (বিকাশ - ৫% ফি)**\n"
    )
    
    await call.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
      
