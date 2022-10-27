import aiohttp
from bs4 import BeautifulSoup
from fake_headers import Headers
import json
import os
import random
import re
from time import time
from vkbottle import Keyboard, KeyboardButtonColor, Text, PhotoMessageUploader, Callback, GroupEventType, ShowSnackbarEvent
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle.modules import logger

# logger.disable("vkbottle")

bot = Bot(os.getenv('TOKEN') or "")
photo_uploader = PhotoMessageUploader(bot.api, generate_attachment_strings=True)

default_keyboard = Keyboard(one_time=False, inline=False)
default_keyboard.add(Text("Поезд"))
default_keyboard.add(Text("Список"))
default_keyboard.row()  # Переходим на следующую строку
default_keyboard.add(Text("Случайное фото"), color=KeyboardButtonColor.POSITIVE)


async def get_image(train_soup: BeautifulSoup, session: aiohttp.ClientSession):
    image_data_raw = train_soup.find('td', {'class': 'pb_photo'})
    images = re.findall(r'/photo/\d\d/\d\d/\d\d/\w+.jpg', str(image_data_raw))
    if len(images) == 0:
        return None
    image_link = images[0].replace('_s', '')
    train_photo = await session.get(f'https://railgallery.ru{image_link}')
    return await photo_uploader.upload(await train_photo.read())


async def get_author(train_soup: BeautifulSoup):
    author_data_raw = train_soup.find('td', {'class': 'pb_descr'}).find('p', {'class': 'sm'})
    for br in author_data_raw.find_all("br"):
        br.replace_with("\n")
    return author_data_raw.get_text().split('\n')[-1]  # re.findall(r'/author/\d+/"', str(author_data_raw))


async def get_photo(train_soup: BeautifulSoup, session: aiohttp.ClientSession):
    image = await get_image(train_soup, session)
    if image is None:
        return None, ''
    return image, await get_author(train_soup)


async def get_train_info(train_soup: BeautifulSoup):
    main_table = train_soup.find('td', {'class': 'main'})
    train_name = main_table.find('h1').get_text()
    train_data_raw = main_table.find('table', {'class': 'horlines'}).find_all('tr', {'class': 'h21'})
    train_data_parsed = list(map(lambda x: tuple(map(lambda c: str(c.getText()), x.children)), train_data_raw))
    # noinspection PyTypeChecker
    train_data_dict = dict(train_data_parsed[:-1])
    logger.debug(train_data_dict)
    train_data_dict_filtered = {
        'Дорога приписки': train_data_dict.get('Дорога приписки:'),
        'Депо': train_data_dict.get('Депо:'),
        'Серия': train_data_dict.get('Серия:'),
        'Завод-изготовитель': train_data_dict.get('Завод-изготовитель:'),
        'Построен': train_data_dict.get('Построен:'),
        'Категория': train_data_dict.get('Категория:'),
        'Текущее состояние': train_data_dict.get('Текущее состояние:'),
        'Примечание': train_data_dict.get('Примечание:')
    }
    return train_name, \
           '\n'.join(': '.join(_) for _ in train_data_dict_filtered.items() if _[1] is not None), \
           train_data_parsed[-1][0]


async def get_train(train_num: int, session: aiohttp.ClientSession = None, show_info: bool = True, show_full_info: bool = False):
    if session is None:
        session = aiohttp.ClientSession(headers=Headers(headers=True).generate())

    train_response = await session.get(f'https://railgallery.ru/railcar/{train_num}/', cookies={
        'hidesec': '1',
        'lang': 'ru'
    })
    if 'не найден' in await train_response.text():
        await session.close()
        return {'photo': None, 'message': None}
    train_soup = BeautifulSoup(await train_response.text(), 'html5lib')
    train_name, train_info, train_full_info = await get_train_info(train_soup)
    photo, photo_author = await get_photo(train_soup, session)

    message_text = train_name + '\n'
    if show_info:
        message_text += train_info + '\n\n'
    if show_full_info:
        message_text += train_full_info + '\n\n'
    message_text += photo_author
    await session.close()
    return {'photo': photo, 'message': message_text}


@bot.on.message(text='Случайное фото')
@bot.on.message(text='/random')
async def photo_handler(message: Message):
    data = dict()
    rr = -1
    while data.get('photo') is None:
        rr = random.randint(1, 1000)
        logger.debug(rr)
        data = await get_train(rr, show_info=False)
    more_info_keyboard = (
        Keyboard(inline=True).add(Callback("Больше инфы", payload={"pld": f'{rr}'})).get_json()
    )
    await message.answer(data['message'], attachment=data['photo'], keyboard=more_info_keyboard)


@bot.on.message(regexp=r'/train (.+)')
async def photo_handler(message: Message, match: list):
    train_name = match[0]
    session: aiohttp.ClientSession = aiohttp.ClientSession(headers=Headers(headers=True).generate())
    search_response = await session.get(f'https://railgallery.ru/api.php?action=index-qsearch'
                                        f'&num={train_name}'
                                        f'&exact=1'
                                        f'&_={int(time() * 1000)}')

    train_data = json.loads(await search_response.text())
    data = await get_train(train_data[0]['vid'], session)
    if not session.closed:
        await session.close()
    await message.answer(data['message'], attachment=data['photo'], keyboard=default_keyboard)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent)
@bot.on.message(regexp=r'/info (.+)')
async def photo_handler(message: Message, match: list = None):
    session: aiohttp.ClientSession = aiohttp.ClientSession(headers=Headers(headers=True).generate())
    if type(message) is Message:
        train_name = match[0]
        search_response = await session.get(f'https://railgallery.ru/api.php?action=index-qsearch'
                                            f'&num={train_name}&exact=1&_={int(time() * 1000)}')
        train_data = json.loads(await search_response.text())
        train_num = train_data[0]['vid']
    else:
        train_num = message.payload['pld']
    data = await get_train(train_num, session, True, True)
    if not session.closed:
        await session.close()
    if type(message) is Message:
        await message.answer(data['message'], attachment=data['photo'], keyboard=default_keyboard)
    else:
        from vkbottle.tools.dev.mini_types.bot import MessageEventMin
        message: MessageEventMin
        await message.send_message_event_answer(
                event_id=message.object.event_id,
                user_id=message.object.user_id,
                peer_id=message.object.peer_id,
                event_data=ShowSnackbarEvent(text="Поиск информации о поезде"))
        await message.send_message(data['message'], keyboard=default_keyboard.get_json())


@bot.on.message(regexp=r'/photo (.+)')
async def photo_handler(message: Message, match: list):
    train_name = match[0]
    session: aiohttp.ClientSession = aiohttp.ClientSession(headers=Headers(headers=True).generate())
    search_response = await session.get(f'https://railgallery.ru/api.php?action=index-qsearch'
                                        f'&num={train_name}'
                                        f'&exact=1'
                                        f'&_={int(time() * 1000)}')

    train_data = json.loads(await search_response.text())
    data = await get_train(train_data[0]['vid'], session, show_info=False)
    if not session.closed:
        await session.close()
    await message.answer(data['message'], attachment=data['photo'], keyboard=default_keyboard)


@bot.on.message(text='Поезд')
@bot.on.message(text='Список')
async def silly_buttons(message: Message):
    return 'Я не знаю, что эти кнопки должны были делать, а прошлый разработчик не хочет говорить'


@bot.on.message()
async def handler(message: Message):
    global default_keyboard
    await message.answer('Для общения с ботом используй кнопки или команды:\n'
                         '/train - найти фото и информацию о поезде\n'
                         '/photo - последнее фото поезда\n'
                         '/info - вся информация о поезде\n'
                         '/random - случайное фото', keyboard=default_keyboard)


if __name__ == '__main__':
    bot.run_forever()
