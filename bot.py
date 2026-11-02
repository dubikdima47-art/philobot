"""
Філобот — переписує коротке повідомлення у довгу "філософську"/рофляну версію.
Працює на безкоштовному Gemini API (Google AI Studio).

Встановлення:
    pip install aiogram google-genai

Запуск:
    export TELEGRAM_BOT_TOKEN="..."
    export GEMINI_API_KEY="..."
    python bot.py
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Ти — гумористичний переписувач коротких повідомлень українською. "
    "Тобі дають коротку фразу (наприклад 'привіт'), а ти перетворюєш її "
    "на довгий, трохи пафосний, псевдофілософський монолог у рофляному стилі, "
    "ніби це репліка з дешевого філософського трактату або мему. "
    "Зберігай суть оригінального повідомлення, але роздувай її до 3-6 речень. "
    "Можна додавати іронію, абсурдні порівняння, риторичні питання. "
    "Відповідай ТІЛЬКИ переписаним текстом, без пояснень і без лапок."
)


def rewrite_text(original: str) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=original,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=600,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return (response.text or "").strip()


async def safe_rewrite(message: Message, text: str):
    try:
        # to_thread, щоб бот не "вис" поки Gemini думає
        rewritten = await asyncio.to_thread(rewrite_text, text)
    except Exception:
        logging.exception("Gemini error")
        await message.reply("Щось пішло не так з Gemini 😅 Спробуй ще раз трохи пізніше.")
        return
    if not rewritten:
        await message.reply("Gemini нічого не відповів. Спробуй переформулювати.")
        return
    await message.reply(rewritten)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привіт! Напиши мені будь-яку коротку фразу, і я перетворю її "
        "на щось значно довше та філософськіше 😄\n\n"
        "В груповому чаті: згадай мене (@ім'я_бота текст)."
    )


@dp.message(Command("rofl"))
async def rofl_command(message: Message):
    text = message.text.replace("/rofl", "", 1).strip()
    if not text:
        await message.answer("Напиши текст після команди, напр.: /rofl привіт")
        return
    await safe_rewrite(message, text)


@dp.message(F.text)
async def any_text_handler(message: Message):
    # У приваті реагуємо на будь-яке повідомлення.
    # У групі реагуємо тільки якщо бота згадали (@ім'я) або відповіли на його повідомлення.
    bot_username = (await bot.get_me()).username
    is_private = message.chat.type == "private"
    is_mention = bot_username and f"@{bot_username}" in (message.text or "")
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.is_bot
    )

    if not (is_private or is_mention or is_reply_to_bot):
        return

    text = message.text
    if is_mention:
        text = text.replace(f"@{bot_username}", "").strip()

    if not text:
        return

    await safe_rewrite(message, text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
   
   
