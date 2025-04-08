import asyncio
import logging
import re
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command

from yt_utils import download_audio  # Importing the download_audio function from yt_utils

import config
from channel_utilis import is_subscribed


dp = Dispatcher()

# Dictionary to store active tasks per user
# This is used to prevent users from spamming multiple download requests
active_tasks: dict[int, asyncio.Task] = {}

# Regular expression pattern to validate YouTube URLs
youtube_url_pattern = r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.*$'

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    # Check if the user is subscribed to the required Telegram channel
    if not await is_subscribed(message.bot, user_id):
        await message.answer(f"❗️Чтобы пользоваться ботом, подпишитесь на наш канал: {config.channel_id}")
        return

    # If a task is already running for this user, cancel it
    if user_id in active_tasks:
        active_tasks[user_id].cancel()

    # Start a new task for processing the YouTube link
    task = asyncio.create_task(process_youtube_link(message))
    active_tasks[user_id] = task


@dp.message(CommandStart())
async def handle_command_start(message: types.Message):
    # Handle the /start command — greet the user and show intro message
    await message.answer(
        f'👋 Привет, {message.from_user.first_name}! Рад видеть тебя здесь.\nДля получения информации о возможностях бота используй команду /help.\nПриятного пользования! 😉'
    )

@dp.message(Command('help'))
async def handle_command_help(message: types.Message):
    # Handle the /help command — describe what the bot can do
    help_text = (
        f'{message.from_user.first_name}, этот бот может скачивать музыку с YouTube.\nПросто отправь ссылку на видео, и я пришлю тебе MP3-файл. 🎶'
    )
    await message.answer(help_text)

@dp.message()
async def handle_message(message: types.Message):
    # This function is triggered for any message
    # Check if a download task already exists for the user
    user_id = message.from_user.id
    if user_id in active_tasks:
        active_tasks[user_id].cancel()

    # Start processing the YouTube link in a background task
    task = asyncio.create_task(process_youtube_link(message))
    active_tasks[user_id] = task

async def process_youtube_link(message: types.Message):
    # This function processes the YouTube link sent by the user

    text = message.text.strip()  # Remove leading/trailing spaces

    # If the text is not a valid YouTube link, show an error
    if not re.match(youtube_url_pattern, text):
        await message.answer("Пожалуйста, отправьте действительную ссылку на YouTube-видео.")
        return

    # Notify the user that the audio is being downloaded
    loading_msg = await message.answer("Скачиваю аудио... 🎧")

    try:
        # Download the audio using a custom utility function
        filepath = download_audio(text)

        # If the file was downloaded and exists
        if filepath and os.path.exists(filepath):
            # Show "uploading" status in the chat
            await message.bot.send_chat_action(
                chat_id=message.chat.id,
                action=ChatAction.UPLOAD_DOCUMENT,
            )
            # Send the MP3 file to the user
            await message.answer_document(
                types.FSInputFile(filepath),
            )

            # Delete the local file after sending
            os.remove(filepath)

            # Clean up: delete original message and "downloading..." message
            await message.delete()
            await loading_msg.delete()
        else:
            await message.answer("❌ Не удалось найти или скачать MP3-файл.")

    except asyncio.CancelledError:
        # If the task is cancelled (e.g. new request from the user), just exit silently
        pass
    except Exception as e:
        # If any other error occurs, send error message to user
        await message.answer(f"❌ Ошибка при загрузке: {e}")

# Main entry point of the bot
async def main():
    logging.basicConfig(level=logging.INFO)  # Enable logging for debugging
    bot = Bot(token=config.token)  # Initialize bot with token from config
    await dp.start_polling(bot)  # Start polling for updates (messages, commands, etc.)

if __name__ == "__main__":
    asyncio.run(main())  # Run the bot
