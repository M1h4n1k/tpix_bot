import aiohttp
from fake_headers import Headers
import orjson
import re
from time import time
from vkbottle import ABCRule
from vkbottle.tools.dev.mini_types.base import BaseMessageMin


class TrainRule(ABCRule[BaseMessageMin]):
    def __init__(self, command: str):
        self.command = command

    async def check(self, event: BaseMessageMin) -> dict | bool:
        groups = re.findall(self.command + r' ([\w\- ]+)', event.text)
        if len(groups):
            session: aiohttp.ClientSession = aiohttp.ClientSession(headers=Headers(headers=True).generate())
            search_response = await session.get(f'https://railgallery.ru/api.php?action=index-qsearch'
                                                f'&num={groups[0]}'
                                                f'&exact=1'
                                                f'&_={int(time() * 1000)}')
            train_num = orjson.loads(await search_response.text())
            await session.close()
            return {'train_num': train_num[0]['vid'] if len(train_num) else -1}
        return False
