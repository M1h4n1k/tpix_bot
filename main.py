import random
from vkbottle import GroupEventType, ShowSnackbarEvent
from vkbottle.bot import Message, MessageEvent
from vkbottle.modules import logger

from loader import bot
from train_parser import get_train
from data.keyboards import get_default_keyboard, get_more_info_keyboard
from data.rules import TrainRule


@bot.on.message(text='Случайное фото')
@bot.on.message(text='/random')
async def photo_handler(message: Message):
    data = dict()
    random_id = -1
    while data.get('photo') is None:
        random_id = random.randint(1, 100000)
        logger.debug(random_id)
        data = await get_train(random_id, show_info=False)
    await message.answer(data['message'], attachment=data['photo'], keyboard=get_more_info_keyboard(random_id))


@bot.on.message(TrainRule('/train'))
async def photo_handler(message: Message, train_num: int = None):
    if train_num == -1:  # Наверно как то можно сделать че-то типа мидлвари на три функции, хз, библиотека уебанская
        return 'Поезд не найден'
    data = await get_train(train_num)
    await message.answer(data['message'], attachment=data['photo'], keyboard=get_default_keyboard())


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent)
@bot.on.message(TrainRule('/info'))
async def photo_handler(message: Message, train_num: int = None):
    if train_num == -1:
        return 'Поезд не найден'
    if message.payload is not None:
        train_num = message.payload['pld']
    data = await get_train(train_num, show_info=True, show_full_info=True)
    if type(message) is Message:
        await message.answer(data['message'], attachment=data['photo'], keyboard=get_default_keyboard())
    else:
        await message.send_message_event_answer(
                event_id=message.object.event_id,
                user_id=message.object.user_id,
                peer_id=message.object.peer_id,
                event_data=ShowSnackbarEvent(text="Поиск информации о поезде"))
        await message.send_message(data['message'], keyboard=get_default_keyboard())


@bot.on.message(TrainRule('/photo'))
async def photo_handler(message: Message, train_num: int = None):
    if train_num == -1:
        return 'Поезд не найден'
    data = await get_train(train_num, show_info=False)
    await message.answer(data['message'], attachment=data['photo'], keyboard=get_default_keyboard())


@bot.on.message(text='Поезд')
@bot.on.message(text='Список')
async def silly_buttons(message: Message):
    return 'Я не знаю, что эти кнопки должны были делать, а прошлый разработчик не хочет говорить'


@bot.on.message()
async def handler(message: Message):
    await message.answer('Для общения с ботом используй кнопки или команды:\n'
                         '/train - найти фото и информацию о поезде\n'
                         '/photo - последнее фото поезда\n'
                         '/info - вся информация о поезде\n'
                         '/random - случайное фото', keyboard=get_default_keyboard())


if __name__ == '__main__':
    bot.run_forever()
