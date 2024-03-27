# -*- coding: utf-8 -*-
"""
Telegram posts bot
Version: 0.2
Python: 3.10
OS: Manjaro Linux (6.6.19-1-MANJARO)
Designed for @muqesq by MrWoon
"""
import re
import json
import random

from modules.logger import Logger

import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup

# Переменные
logger = Logger("Bot", "logs.txt")
logger.log('info', "Создание классов и функций..")
db = {}
stats24 = '0:0'
codes = []
dp = Dispatcher()
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📝 Создать пост"),
            KeyboardButton(text="🗑️ Удалить пост"),
            KeyboardButton(text="✉️ Отправить пост"),
            KeyboardButton(text="📋 Список постов"),
        ],
        [
            KeyboardButton(text="🔗 Создать ссылку"),
            KeyboardButton(text="❌ Удалить ссылку"),
            KeyboardButton(text="🌐 Список ссылок"),
            KeyboardButton(text="📊 Статистика")
        ]
    ]
)
stop_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❌ Отмена")
        ]
    ]
)


# FSM
class AddPost(StatesGroup):
    name = State()
    picture = State()
    button1 = State()
    button2 = State()
    content = State()


class RemovePost(StatesGroup):
    name = State()
    confirm = State()
    post = State()


class SendPost(StatesGroup):
    name = State()
    users = State()
    preview = State()


class PreviewPost(StatesGroup):
    name = State()


class AddLink(StatesGroup):
    link = State()


class DeleteLink(StatesGroup):
    link = State()


# Функции
def update_db(file_path: str, mode: str) -> bool:
    """
    Обновляет базу данных.

    :param file_path: Путь к файлу базы данных.
    :type file_path: str
    :param mode: Режим работы функции ('w' для записи, 'r' для чтения).
    :type mode: str
    :return: Возвращает True при успехе и False при ошибки.
    :rtype: bool
    """
    global db
    if mode == 'w':
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
            return True
    elif mode == 'r':
        with open(file_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
            return True
    else:
        return False


async def clear_stats():
    global stats24
    while True:
        await asyncio.sleep(24 * 3600)
        stats24 = 0


update_db('db.json', 'r')
bot = Bot(db['settings']['token'], default=DefaultBotProperties(parse_mode='HTML'))

logger.log('info', 'Создание обработчиков команд..')


async def send_post(post: dict, chat_id: int) -> bool:
    '''
    Отправить пост в чат

    :param post: Словарь с данными поста
    :param chat_id: Айди чата
    :return: True при усепехе и False при ошибки
    '''

    if db['settings']['DEBUG_MODE'] == 1:
        logger.log('warn', f"send_post({str(post)}, {str(chat_id)})")

    buttons = []
    if post['button1'] is not None:
        buttons.append([InlineKeyboardButton(text=post['button1'][0], url=post['button1'][1])])
    if post['button2'] is not None:
        buttons.append([InlineKeyboardButton(text=post['button2'][0], url=post['button2'][1])])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await bot.send_photo(chat_id=chat_id, photo=post['picture'], caption=post['content'], reply_markup=kb)
        return True
    except:
        return False


@dp.message(Command('start'))
async def start(message: Message):
    """
    Обработчик команды /start
    """
    global stats24

    auth = False
    code = message.text.split(' ')[-1]
    if code in db['codes']:
        auth = True
    else:
        auth = False
    if db['settings']['DEBUG_MODE'] == 1:
        logger.log('warn', f'start() от @{message.from_user.username}')
    if message.from_user.id not in [user["id"] for user in db['users']]:
        if auth:
            db['users'].append({"name": message.from_user.username, "id": message.from_user.id})
            update_db('db.json', 'w')
            try:
                post_indices = random.sample(range(len(db['posts'])), int(db['settings']['random_posts'] + 1))
                for post_index in post_indices:
                    await send_post(db['posts'][post_index], message.chat.id)
            except:
                pass

            if db['settings']['DEBUG_MODE'] == 1:
                logger.log('warn', f'Новый пользователь: @{message.from_user.username}')

            with open("stats.txt", 'r', encoding='utf-8') as f2:
                stat = f2.read().split(':')
                with open("stats.txt", 'w', encoding='utf-8') as f:
                    f.write(str(int(stat[0]) + 1) + f':{stat[1]}')
            stats24 = str(int(stats24.split(':')[0]) + 1) + f":{stats24[1]}"
            await message.answer("Вы успешно подписались на посты!")
        else:
            await message.answer(
                f"Данный бот является приватным. Для доступа к нему попросите ссылку у @{db['settings']['admin']}")
    else:
        await message.answer("Вы уже подписаны на посты.")
        if db['settings']['DEBUG_MODE'] == 1:
            logger.log('warn', f'Попытка повторого запуска: @{message.from_user.username}')

    if message.from_user.username == db['settings']['admin']:
        await message.answer(f"Добро пожаловать, администратор @{db['settings']['admin']}!", reply_markup=admin_kb)
        logger.log('warn', f'Обнаружен админ: @{message.from_user.username}')


@dp.message(F.text.casefold().in_(['/add_post', "📝 создать пост"]))
async def add_post(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /add_post
    """
    if message.from_user.username == db['settings']['admin']:
        await state.set_state(AddPost.name)
        await message.answer(
            "Введите имя поста (для базы данных)", reply_markup=stop_kb)


# ДПВК для /add_post
@dp.message(AddPost.name)
async def post_name(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.update_data(name=message.text)
    await state.set_state(AddPost.picture)
    await message.answer(
        "Отправьте картинку поста (Если вы с ПК - отправляйте с сжатием, вторым вариантом)", reply_markup=stop_kb)


@dp.message(AddPost.picture, F.photo)
async def post_photo(message: Message, state: FSMContext):
    try:
        if message.text.strip().lower() == '❌ отмена':
            await state.clear()
            await message.answer("Действие отменено.", reply_markup=admin_kb)
            return 0
    except:
        pass
    await state.update_data(picture=message.photo[-1].file_id)
    await state.set_state(AddPost.content)
    await message.answer("Введите текст поста", reply_markup=stop_kb)

@dp.message(AddPost.picture, F.text)
async def post_photo_non_pic(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    else:
        await message.answer("Пожалуйста, отправьте фотографию, а не текст.")


@dp.message(AddPost.content)
async def post_content(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.update_data(content=message.text)
    await state.set_state(AddPost.button1)
    await message.answer(
        "Введите данные о первой кнопке в формате 'Текст + Ссылка' (либо 'none', если кнопка не нужна)",
        reply_markup=stop_kb)


@dp.message(AddPost.button1)
async def post_button1(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    if not re.match(r'^[^|]+? \+ (https?://\S+)$', message.text.strip()) and message.text.strip().lower() != "none":
        await message.answer(
            "Неверный формат данных о кнопке. Пожалуйста, используйте формат 'Текст + Ссылка' (с https://) и повторите попытку.",
            reply_markup=stop_kb)
    else:
        await state.update_data(button1=message.text)
        await state.set_state(AddPost.button2)
        await message.answer(
            "Введите данные о второй кнопке в формате 'Текст + Ссылка' (либо 'none', если кнопка не нужна)",
            reply_markup=stop_kb)


@dp.message(AddPost.button2)
async def post_button2(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    if not re.match(r'^[^|]+? \+ (https?://\S+)$', message.text.strip()) and message.text.strip().lower() != "none":
        await message.answer(
            "Неверный формат данных о кнопке. Пожалуйста, используйте формат 'Текст + Ссылка' (с https://) и повторите "
            "попытку.", reply_markup=stop_kb)
    else:
        await state.update_data(button2=message.text)
        data = await state.get_data()
        await state.clear()

        if data['button1'].lower() == "none":
            data["button1"] = None
        else:
            data['button1'] = data['button1'].split(' + ')

        if data['button2'].lower() == "none":
            data["button2"] = None
        else:
            data['button2'] = data['button2'].split(' + ')

        db['posts'].append(data)
        update_db('db.json', 'w')
        await message.answer("Пост успешно создан!", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/remove_post', "🗑️ удалить пост"]))
async def remove_post(message: Message, state: FSMContext):
    '''
    Обраточик для команды /remove_post
    '''
    if message.from_user.username == db['settings']['admin']:
        await state.set_state(RemovePost.name)
        await message.answer("Введите название поста для удаления", reply_markup=stop_kb)


# ДПВК для /remove_post
@dp.message(RemovePost.name)
async def remove_post_name(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.update_data(name=message.text)
    await state.set_state(RemovePost.confirm)
    data = await state.get_data()
    gpost = {}
    for post in db["posts"]:
        if data['name'].lower() in post['name'].lower():
            update_db('db.json', 'r')
            gpost = post
    if gpost != {}:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Да'),
                    KeyboardButton(text='Нет')
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Вы уверены, что хотите удалить пост? Предпросмотр поста:", reply_markup=kb)
        await state.update_data(post=gpost)
        await send_post(gpost, message.chat.id)
    else:
        await message.answer("Пост не найден.", reply_markup=admin_kb)


@dp.message(RemovePost.confirm)
async def remove_post_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    if message.text == "Да":
        db['posts'] = [post for post in db['posts'] if post["name"].lower() != data['name'].lower()]
        update_db('db.json', 'w')
        await message.answer("<s>Этот пост был из тех.. Кто просто любит жить..</s>\nПост успешно удалён.",
                             reply_markup=admin_kb)
    else:
        await message.answer("Удаление поста отменено.", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/send_post', "✉️ отправить пост"]))
async def send_post_cmd(message: Message, state: FSMContext):
    if message.from_user.username == db['settings']['admin']:
        await state.set_state(SendPost.users)
        await message.answer("Введите название поста для отправки", reply_markup=stop_kb)


# ДПВК для /send_post
@dp.message(SendPost.users)
async def send_post_users(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.update_data(name=message.text)
    await state.set_state(SendPost.name)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Отправить всем'),
                KeyboardButton(text='❌ Отмена')
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "Кому вы хотите отправить пост? (Напишите юзернеймы через запятую без @ (Пример: bob,sonya,vasya). Для отправки всем пользователям введите или нажмите кнопку \"Отправить всем\".)",
        reply_markup=kb)


@dp.message(SendPost.name)
async def send_post_name(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.update_data(users=message.text)
    await state.set_state(SendPost.preview)
    data = await state.get_data()
    gpost = {}
    for post in db["posts"]:
        if data['name'].lower() in post['name'].lower():
            gpost = post
    if gpost != {}:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Да'),
                    KeyboardButton(text='Нет')
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Вы уверены, что хотите отправить пост? Предпросмотр поста:", reply_markup=kb)
        await state.update_data(preview=gpost)
        await send_post(gpost, message.chat.id)
    else:
        await message.answer("Пост не найден.", reply_markup=admin_kb)


@dp.message(SendPost.preview)
async def send_post_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    if message.text == "Да":
        if data['users'].lower() == "отправить всем":
            update_db('db.json', 'r')
            for chat_id in [user["id"] for user in db['users']]:
                print(chat_id)
                await send_post(data['preview'], chat_id)
        else:
            users = data['users'].split(',')
            for user in users:
                for user2 in db['users']:
                    if user2["name"] == user:
                        await send_post(data['preview'], user2['id'])
        await message.answer("Пост успешно отправлен!", reply_markup=admin_kb)
    else:
        await message.answer("Отправка поста отменена.", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/posts_list', "📋 список постов"]))
async def post_list_cmd(message: Message):
    '''
    Обработчик команды /posts_list
    '''
    if message.from_user.username == db['settings']['admin']:
        p = 1
        for post in db['posts']:
            await message.answer(f'''Номер поста: {str(p)}
Название поста: {post['name']}''')
            p += 1
        if db['posts'] == []:
            await message.answer("Вы ещё не создали не одного поста.")
        else:
            await message.answer("Для просмотра любого поста введите /preview", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/preview']))
async def preview_cmd(message: Message, state: FSMContext):
    if message.from_user.username == db['settings']['admin']:
        await state.set_state(PreviewPost.name)
        await message.answer("Введите имя поста который вы хотите увидеть")


@dp.message(PreviewPost.name)
async def preview_post(message: Message, state: FSMContext):
    await state.clear()

    gpost = {}
    for post in db["posts"]:
        if message.text.lower() in post['name'].lower():
            gpost = post
    if gpost != {}:
        await message.answer("Предпросмотр поста:")
        await send_post(gpost, message.chat.id)
    else:
        await message.answer("Пост не найден.")


@dp.message(F.text.casefold().in_(['/add_link', "🔗 создать ссылку"]))
async def add_link_cmd(message: Message, state: FSMContext):
    '''
    Обработчик команды /add_link
    '''
    await state.set_state(AddLink.link)
    await message.answer(text=f"Придумайте код для ссылки которую нужно создать", reply_markup=stop_kb)


# ДПВК для /add_link
@dp.message(AddLink.link)
async def add_link(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.clear()
    code = message.text.strip()
    if code in db['codes']:
        await message.answer("Ссылка уже существует.")
    else:
        db['codes'].append(code)
        update_db('db.json', 'w')
        username = (await bot.get_me()).username
        link = f"https://t.me/{username}?start={code}"
        await message.answer(text=f"Ссылка: {link}", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/delete_link', "❌ удалить ссылку"]))
async def delete_link_cmd(message: Message, state: FSMContext):
    '''
    Обработчик команды /delete_link
    '''
    await state.set_state(DeleteLink.link)
    await message.answer(text=f"Введите ссылку (с https://) которую нужно удалить", reply_markup=stop_kb)


# ДПВК для /delete_link
@dp.message(DeleteLink.link)
async def delete_link(message: Message, state: FSMContext):
    if message.text.strip().lower() == '❌ отмена':
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=admin_kb)
        return 0
    await state.clear()
    code = message.text.split('?start=')[1].strip()
    if code in db['codes']:
        db['codes'].remove(code)
        update_db('db.json', 'w')
        await message.answer("Ссылка удалена.", reply_markup=admin_kb)
    else:
        await message.answer("Ссылка не найдена.", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/links', "🌐 список ссылок"]))
async def links(message: Message):
    '''
    Обработчик команды /links
    '''
    username = (await bot.get_me()).username
    c = 1
    for code in db['codes']:
        link = f"https://t.me/{username}?start={code}"
        await message.answer(f"Ссылка {str(c)}: {link}", reply_markup=admin_kb)
        c += 1
    if not db['codes']:
        await message.answer("Вы ещё не создали не одной ссылки на бота.", reply_markup=admin_kb)


@dp.message(F.text.casefold().in_(['/stats', "📊 статистика"]))
async def links(message: Message):
    '''
    Обработчик команды /stats
    '''
    with open('stats.txt', 'r', encoding='utf-8') as f:
        stats = f.read().strip()
    await message.answer(f'''
<b>Статистика</b>
За 24 часа
- Входов: {stats24.split(':')[0]}
- Выходов: {stats24.split(':')[1]}
За всё время
- Входов: {stats.split(':')[0]}
- Выходов: {stats.split(':')[1]}
''', reply_markup=admin_kb)


logger.log('info', 'Запуск бота..')


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def left_member(event: ChatMemberUpdated):
    global stats24

    with open("stats.txt", 'r', encoding='utf-8') as f2:
        stat = f2.read().split(':')
        with open("stats.txt", 'w', encoding='utf-8') as f:
            f.write(f'{stat[0]}:' + str(int(stat[1]) + 1))
    stats24 = f"{stats24[0]}:" + str(int(stats24.split(':')[1]) + 1)


# Запуск бота
async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    task = asyncio.create_task(clear_stats())
    logger.log('info', 'Бот готов к работе')
    await dp.start_polling(bot)
    logger.log('critical', 'Бот отключён')


if __name__ == "__main__":
    asyncio.run(main())
    update_db('db.json', 'w')
