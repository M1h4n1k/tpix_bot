import aiohttp
from bs4 import BeautifulSoup
import re
from loader import photo_uploader
from vkbottle.modules import logger
from fake_headers import Headers


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