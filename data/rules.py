import aiohttp
from fake_headers import Headers
import re
from vkbottle import ABCRule
from vkbottle.tools.dev.mini_types.base import BaseMessageMin
from train_parser import get_train_num


class TrainRule(ABCRule[BaseMessageMin]):
    def __init__(self, command: str):
        self.command = command

    async def check(self, event: BaseMessageMin) -> dict | bool:
        groups = re.findall(self.command + r' ([\w\- ]+)', event.text)
        if len(groups):
            return {'train_num': get_train_num(groups[0])}
        return False
