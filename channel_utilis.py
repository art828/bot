from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import config

CHANNEL_ID = config.channel_id

async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        # Getting information about a user in a channel
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        # Checking the subscription status
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except TelegramBadRequest as e:
        # The error can be caused by various reasons, for example, if the user hides their status
        print(f"Ошибка при проверке подписки: {e}")
        return False
