from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback


def get_default_keyboard():
    default_keyboard = Keyboard(one_time=False, inline=False)
    default_keyboard.add(Text("Поезд")).add(Text("Список"))
    default_keyboard.row()
    default_keyboard.add(Text("Случайное фото"), color=KeyboardButtonColor.POSITIVE)
    return default_keyboard


def get_more_info_keyboard(train_id):
    return Keyboard(inline=True).add(Callback("Больше инфы", payload={"pld": f'{train_id}'}))
