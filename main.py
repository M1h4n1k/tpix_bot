import random
from vkbottle import GroupEventType, ShowSnackbarEvent
from vkbottle.bot import Message, MessageEvent
from vkbottle.modules import logger

from loader import bot
from train_parser import get_train, get_train_num
from data.keyboards import get_default_keyboard, get_more_info_keyboard
from data.rules import TrainRule
from data.states import TrainState
from data.texts import help_message


@bot.on.message(text='/back')
async def handler(message: Message):
    if await bot.state_dispenser.get(message.peer_id):
        await bot.state_dispenser.delete(message.peer_id)
    await message.answer(help_message, keyboard=get_default_keyboard())


@bot.on.message(text='Случайное фото')
@bot.on.message(text='/random')
async def photo_handler(message: Message):
    data = dict()
    random_id = -1
    while data.get('photo') is None:
        random_id = random.randint(1, 100000)
        logger.debug(random_id)
        data = await get_train(random_id, show_info=False)
    return {
        'message': data['message'],
        'attachment': data['photo'],
        'keyboard': get_more_info_keyboard(random_id)
    }


@bot.on.message(TrainRule('/train'))
@bot.on.message(state=TrainState.select_train_state)
async def photo_handler(message: Message, train_num: int = None):
    if await bot.state_dispenser.get(message.peer_id):
        await bot.state_dispenser.delete(message.peer_id)
        train_num = await get_train_num(message.text)
    if train_num == -1:  # Наверно как то можно сделать че-то типа мидлвари на три функции, хз, библиотека уебанская
        # проверка работы коммитов
        return 'Поезд не найден'
    data = await get_train(train_num)
    return {
        'message': data['message'],
        'attachment': data['photo'],
        'keyboard':get_default_keyboard()
    }


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
    return {
        'message': data['message'],
        'attachment': data['photo'],
        'keyboard': get_default_keyboard()
    }


@bot.on.message(text='Поезд')
async def train_button(message: Message):
    await bot.state_dispenser.set(message.peer_id, TrainState.select_train_state)
    return 'Напиши название поезда, можно неполное\nДля отмены напиши /back'


@bot.on.message(text='Список')
async def silly_buttons(message: Message):
    return 'Я не хочу читать код прошлого разработчика'


@bot.on.message()
async def handler(message: Message):
    await message.answer(help_message, keyboard=get_default_keyboard())


if __name__ == '__main__':
    bot.run_forever()
