import asyncio
import logging
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command

from yt_utils import download_audio
from channel_utilis import is_subscribed
import config

dp = Dispatcher()
active_tasks: dict[int, asyncio.Task] = {}
youtube_url_pattern = r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.*$'

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f'👋 Привет, {message.from_user.first_name}!\n'
        'Для помощи используй /help.\nПриятного пользования! 😉'
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        f'{message.from_user.first_name}, отправь ссылку на YouTube-видео, и я пришлю тебе MP3-файл 🎶'
    )

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if not await is_subscribed(message.bot, user_id):
        await message.answer(f"❗️Подпишитесь на канал: {config.channel_id}")
        return

    if user_id in active_tasks:
        active_tasks[user_id].cancel()

    active_tasks[user_id] = asyncio.create_task(process_youtube_link(message))

async def process_youtube_link(message: types.Message):
    url = message.text.strip()

    if not re.match(youtube_url_pattern, url):
        await message.answer("❗️Отправьте действительную ссылку на YouTube-видео.")
        return

    loading_msg = await message.answer("Скачиваю аудио... 🎧")

    try:
        filepath = download_audio(url)

        if filepath and os.path.exists(filepath):
            await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
            await message.answer_document(types.FSInputFile(filepath))
            os.remove(filepath)
            await message.delete()
            await loading_msg.delete()
        else:
            await message.answer("❌ Не удалось скачать MP3-файл.")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.token)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())