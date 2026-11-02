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
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://telegram-bot-1-f76m.onrender.com")

MONETAG_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monetag Ads</title>
    <script src='//libtl.com/sdk.js' data-zone='12176564' data-sdk='show_12176564'></script>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #0f172a; color: #fff; padding: 20px; margin: 0; }
        .btn { background: #3b82f6; color: white; border: none; padding: 14px 24px; font-size: 16px; border-radius: 10px; cursor: pointer; margin-top: 20px; text-decoration: none; display: inline-block; font-weight: bold; width: 85%; max-width: 320px; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-top: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        h1 { color: #38bdf8; font-size: 22px; }
        .warning { background: #ef4444; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; display: none; font-size: 14px; font-weight: bold; }
    </style>
</head>
<body>
    <div id="adblock-warning" class="warning">⚠️ সতর্কতা: অ্যাডব্লকার বন্ধ করুন!</div>
    <h1>🎯 Monetag Rewarded Ads</h1>
    <div class="card">
        <p>রেট: <b>৳ ১.৫০</b> | লিমিট: <b>৩০টি/দিন</b></p>
        <p>ব্যালেন্স: <b id="balance" style="color: #4ade80; font-size: 20px;">৳ 0.00</b></p>
        <button class="btn" onclick="watchAd()">👀 Monetag অ্যাড দেখুন</button>
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
                    fetch('/reward?type=monetag&user_id=' + userId)
                        .then(res => res.json())
                        .then(data => {
                            if(data.status === 'success') {
                                alert('🎉 অভিনন্দন! ১.৫০ টাকা যোগ হয়েছে।');
                                document.getElementById('balance').innerText = '৳ ' + data.balance.toFixed(2);
                            } else {
                                alert(data.message);
                            }
                        }).catch(err => {
                            alert('সার্ভারে সমস্যা হয়েছে।');
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

ADSTERRA_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adsterra Native Ads</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #0f172a; color: #fff; padding: 20px; margin: 0; }
        .btn { background: #10b981; color: white; border: none; padding: 14px 24px; font-size: 16px; border-radius: 10px; cursor: pointer; margin-top: 20px; text-decoration: none; display: inline-block; font-weight: bold; width: 85%; max-width: 320px; }
        .btn:disabled { background: #64748b; cursor: not-allowed; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        h1 { color: #34d399; font-size: 22px; }
        .native-ad-box { background: #334155; padding: 15px; border-radius: 12px; margin-top: 15px; min-height: 120px; display: flex; align-items: center; justify-content: center; }
    </style>
</head>
<body>
    <h1>💎 Adsterra Native Ads</h1>
    <div class="card">
        <p>রেট: <b>৳ ১.৫০</b> | লিমিট: <b>১৫টি/দিন</b></p>
        <p>ব্যালেন্স: <b id="balance" style="color: #4ade80; font-size: 20px;">৳ 0.00</b></p>
        
        <div class="native-ad-box" id="ad-container">
            <div id="container-fdd24f280dc0789b50029181f039ea62">লোড হচ্ছে...</div>
        </div>

        <button id="claim-btn" class="btn" disabled onclick="claimReward()">⏳ ১০ সেকেন্ড অপেক্ষা করুন...</button>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || '0';
        let countdown = 10;
        let timerInterval;

        function loadAdScript() {
            const container = document.getElementById('ad-container');
            container.innerHTML = '<div id="container-fdd24f280dc0789b50029181f039ea62"></div>';

            const oldScript = document.querySelector('script[src*="biomanos.org"]');
            if (oldScript) oldScript.remove();

            const script = document.createElement('script');
            script.async = true;
            script.dataset.cfasync = "false";
            script.src = "https://biomanos.org/21/fdd24f280dc0789b50029181f039ea62";
            document.body.appendChild(script);

            startTimer();
        }

        function startTimer() {
            countdown = 10;
            const btn = document.getElementById('claim-btn');
            btn.disabled = true;

            if (timerInterval) clearInterval(timerInterval);

            timerInterval = setInterval(() => {
                countdown--;
                if (countdown > 0) {
                    btn.innerText = `⏳ রিওয়ার্ড পেতে ${countdown} সেকেন্ড অপেক্ষা করুন`;
                } else {
                    clearInterval(timerInterval);
                    btn.disabled = false;
                    btn.innerText = "✅ রিওয়ার্ড নিন ও নতুন অ্যাড আনুন";
                }
            }, 1000);
        }

        function claimReward() {
            fetch('/reward?type=adsterra&user_id=' + userId)
                .then(res => res.json())
                .then(data => {
                    if(data.status === 'success') {
                        alert('🎉 সফল! ১.৫০ টাকা যোগ হয়েছে।');
                        document.getElementById('balance').innerText = '৳ ' + data.balance.toFixed(2);
                        loadAdScript(); // নতুন অ্যাড এবং টাইমার রিস্টার্ট হবে
                    } else {
                        alert(data.message);
                    }
                }).catch(err => {
                    alert('সার্ভারে সমস্যা হয়েছে।');
                });
        }

        // পেজ লোড হওয়ার সাথে সাথে প্রথম অ্যাড লোড করা
        window.onload = function() {
            loadAdScript();
        };
    </script>
</body>
</html>
"""

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/monetag':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MONETAG_HTML.encode('utf-8'))
            return
            
        elif path == '/adsterra':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ADSTERRA_HTML.encode('utf-8'))
            return

        elif path == '/reward':
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
        self.wfile.write(MONETAG_HTML.encode('utf-8'))

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

API_TOKEN = '9042324215:AAFxdjD5S6I2AKWiHj079mjSh7jDcVlp0Zg'
ADMIN_ID = 0  
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

class WithdrawState(StatesGroup):
    waiting_for_number = State()
    waiting_for_amount = State()

def check_and_reset_limit(user_id):
    today = datetime.now().date().isoformat()
    if user_last_date.get(user_id) != today:
        user_last_date[user_id] = today
        direct_ad_counts[user_id] = 0

@dp.message(Command("start"))
async def send_welcome(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
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

    monetag_url = f"{RENDER_URL}/monetag?user_id={user_id}"
    adsterra_url = f"{RENDER_URL}/adsterra?user_id={user_id}"
    
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    watched_direct = direct_ad_counts.get(user_id, 0)
    remaining_direct = 10 - watched_direct

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 পেমেন্ট গ্রুপে জয়েন করুন (বাধ্যতামূলক)", url=PAYMENT_GROUP_URL)],
        [InlineKeyboardButton(text="🎯 Monetag অ্যাড দেখুন (৳১.৫০)", web_app=WebAppInfo(url=monetag_url))],
        [InlineKeyboardButton(text="💎 Adsterra নেটিভ অ্যাড দেখুন (৳১.৫০)", web_app=WebAppInfo(url=adsterra_url))],
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
        f"💎 Adsterra নেটিভ অ্যাড: **৳ ১.৫০ (সর্বোচ্চ ১৫টি/দিন - অটো রিফ্রেশ ও টাইমার)**\n"
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
async def withdraw_bkash(call: types.CallbackQuery, state: FSMContext):
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
        await call.answer()
        return

    await state.set_state(WithdrawState.waiting_for_number)
    await call.message.edit_text(
        "📱 অনুগ্রহ করে আপনার **বিকাশ নম্বরটি** লিখুন (যেমন: 017xxxxxxxx):",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(WithdrawState.waiting_for_number)
async def process_bkash_number(message: types.Message, state: FSMContext):
    bkash_num = message.text.strip()
    await state.update_data(bkash_number=bkash_num)
    await state.set_state(WithdrawState.waiting_for_amount)
    
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0.00)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    await message.answer(
        f"💵 আপনার বর্তমান ব্যালেন্স: ৳ {balance:.2f}\n\n"
        f"আপনি কত টাকা উইথড্র করতে চান? (ন্যূনতম ৮৫০ টাকা এবং আপনার মোট ব্যালেন্সের মধ্যে লিখুন):",
        reply_markup=keyboard
    )

@dp.message(WithdrawState.waiting_for_amount)
async def process_bkash_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0.00)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 মূল মেনু", callback_data="back_home")]
    ])
    
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ সঠিক অঙ্কের অ্যামাউন্ট লিখুন (যেমন: 850 বা 1000)। আবার চেষ্টা করুন:", reply_markup=keyboard)
        return

    if amount < 850.00 or amount > balance:
        await message.answer(f"❌ ভুল অ্যামাউন্ট! ন্যূনতম ৮৫০ টাকা এবং আপনার বর্তমান ব্যালেন্স (৳ {balance:.2f})-এর বেশি উইথড্র করা যাবে না। সঠিক অ্যামাউন্ট লিখুন:", reply_markup=keyboard)
        return

    data = await state.get_data()
    bkash_number = data.get('bkash_number')
    await state.clear()

    user_balances[user_id] = balance - amount
    extra_amount = amount - 850.00

    success_msg = (
        f"✅ **বিকাশ উইথড্র রিকোয়েস্ট সফল হয়েছে!**\n\n"
        f"📱 বিকাশ নম্বর: `{bkash_number}`\n"
        f"💵 উইথড্র অ্যামাউন্ট: ৳ {amount:.2f}\n"
        f"📅 প্রতি মাসের ১৭-১৯ তারিখ ও ১-৩ তারিখের মধ্যে পেমেন্ট দেওয়া হবে।"
    )
    await message.answer(success_msg, reply_markup=keyboard, parse_mode="Markdown")

    admin_notify_text = (
        f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n\n"
        f"👤 ইউজার ID: `{user_id}`\n"
        f"👤 নাম: {message.from_user.full_name}\n"
        f"📱 বিকাশ নম্বর: `{bkash_number}`\n"
        f"💵 উইথড্র অ্যামাউন্ট: ৳ {amount:.2f}\n"
    )
    if extra_amount > 0:
        admin_notify_text += f"💎 অতিরিক্ত ব্যালেন্স (আপনার অ্যাকাউন্টে আসার কথা {ADMIN_USERNAME}): ৳ {extra_amount:.2f}\n"

    try:
        if ADMIN_ID > 0:
            await bot.send_message(ADMIN_ID, admin_notify_text, parse_mode="Markdown")
        else:
            logging.info(f"Admin Notification ({ADMIN_USERNAME}): {admin_notify_text}")
    except Exception as e:
        logging.error(f"Failed to send admin notification: {e}")

@dp.callback_query(lambda c: c.data == "back_home")
async def back_home(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    check_and_reset_limit(user_id)
    balance = user_balances.get(user_id, 0.00)
    refs = user_referrals.get(user_id, 0)
    
    monetag_url = f"{RENDER_URL}/monetag?user_id={user_id}"
    adsterra_url = f"{RENDER_URL}/adsterra?user_id={user_id}"
    
    watched_direct = direct_ad_counts.get(user_id, 0)
    remaining_direct = 10 - watched_direct

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 পেমেন্ট গ্রুপে জয়েন করুন", url=PAYMENT_GROUP_URL)],
        [InlineKeyboardButton(text="🎯 Monetag অ্যাড দেখুন (৳১.৫০)", web_app=WebAppInfo(url=monetag_url))],
        [InlineKeyboardButton(text="💎 Adsterra নেটিভ অ্যাড দেখুন (৳১.৫০)", web_app=WebAppInfo(url=adsterra_url))],
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
        f"💎 Adsterra নেটিভ অ্যাড: **৳ ১.৫০ (সর্বোচ্চ ১৫টি/দিন - অটো রিফ্রেশ ও টাইমার)**\n"
        f"👥 আপনার রেফার: **{refs}/7 টি**\n"
        f"💳 ন্যূনতম উইথড্র: **৮৫০ টাকা (বিকাশ - ৫% ফি)**\n"
    )
    
    await call.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
