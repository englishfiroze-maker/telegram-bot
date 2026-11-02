import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# আপনার বটের টোকেন
API_TOKEN = '9042324215:AAFxdjD5S6I2AKWiHj079mjSh7jDcVlp0Zg'

# আপনার অ্যাড ডাইরেক্ট লিংক
ADS_LINK = 'https://auctionr.org/4/86bc9dc9e2d69c8dd9963e4a821caa82' 

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_balances = {}

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.00
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 অ্যাড দেখে ইনকাম করুন", url=ADS_LINK)],
        [InlineKeyboardButton(text="💰 আমার ওয়ালেট", callback_data="wallet")],
        [InlineKeyboardButton(text="💸 উইথড্র করুন", callback_data="withdraw")]
    ])
    
    welcome_text = (
        f"স্বাগতম {message.from_user.first_name}!\n\n"
        "আমাদের বটে কাজ করে আপনি প্রতিদিন ভালো পরিমাণের টাকা আয় করতে পারবেন।\n"
        "নিচের বাটন থেকে অ্যাড দেখে কাজ শুরু করুন এবং ওয়ালেট চেক করুন।"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "wallet")
async def check_wallet(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = user_balances.get(user_id, 0.00)
    await call.answer(f"আপনার বর্তমান ব্যালেন্স: ৳ {balance}", show_alert=True)

@dp.callback_query(lambda c: c.data == "withdraw")
async def withdraw_request(call: types.CallbackQuery):
    await call.answer("উইথড্র করার জন্য আপনার ন্যূনতম ৫০ টাকা থাকতে হবে।", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
