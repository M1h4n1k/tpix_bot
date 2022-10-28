from vkbottle.bot import Bot
from vkbottle.modules import logger
from vkbottle import PhotoMessageUploader
import os
import sys

# logger.disable("vkbottle")
logger.remove()
logger.add(sys.stderr, level="INFO")

bot = Bot(os.getenv('TOKEN') or "")
photo_uploader = PhotoMessageUploader(bot.api, generate_attachment_strings=True)


