"""
Філобот — переписує коротке повідомлення у довгу "філософську"/рофляну версію.

Як це працює:
1. Пишеш боту в приват, або в груповому чаті згадуєш його: @ім'я_бота текст
2. Бот бере твій текст і просить Claude (або іншу LLM) переписати його
   довше, пафосніше/філософськи, з гумором.
3. Відповідає тим самим повідомленням, тільки "роздутим".

Встановлення:
    pip install aiogram anthropic python-dotenv

Запуск:
    export TELEGRAM_BOT_TOKEN="..."
    export ANTHROPIC_API_KEY="..."
    python bot.py
"""

import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
client = Anthropic(api_key=ANTHROPIC_API_KEY)

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
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": original}],
    )
    return response.content[0].text.strip()


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
    rewritten = rewrite_text(text)
    await message.reply(rewritten)


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

    rewritten = rewrite_text(text)
    await message.reply(rewritten)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
