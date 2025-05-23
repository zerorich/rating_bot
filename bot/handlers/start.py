# bot/handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.database.db import users_collection, messages_collection, ratings_collection
from uuid import uuid4
from datetime import datetime

router = Router()

class InteractionStates(StatesGroup):
    choosing_action = State()
    rating_appearance = State()
    rating_character = State()
    rating_intelligence = State()
    rating_humor = State()
    rating_trust = State()
    wants_relationship = State()
    knows_personally = State()
    asking_for_message = State()
    writing_message = State()
    choosing_anonymity = State()
    waiting_message = State()

@router.message(F.text.startswith("/start send_"))
async def handle_referral(message: Message, state: FSMContext):
    link_id = message.text.replace("/start send_", "").strip()
    
    # Проверяем, существует ли пользователь с таким link_id
    user = await users_collection.find_one({"link_id": link_id})
    if user:
        # Сохраняем информацию о получателе в состоянии
        await state.update_data(recipient_user_id=user['user_id'], recipient_username=user['username'])
        await state.set_state(InteractionStates.choosing_action)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Оценить пользователя", callback_data="start_rating")],
            [InlineKeyboardButton(text="📩 Отправить сообщение", callback_data="send_message")]
        ])
        
        await message.answer(
            f"👤 Вы открыли ссылку пользователя @{user['username']}.\n\n"
            f"Что вы хотите сделать?",
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ Неверная или устаревшая ссылка.")

@router.callback_query(F.data == "send_message")
async def request_message(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipient_username = data.get('recipient_username')
    
    await state.set_state(InteractionStates.waiting_message)
    await callback_query.message.edit_text(
        f"📩 Отправьте анонимное сообщение пользователю @{recipient_username}:\n\n"
        f"Просто напишите текст следующим сообщением."
    )

@router.message(InteractionStates.waiting_message)
async def process_anonymous_message(message: Message, state: FSMContext):
    data = await state.get_data()
    recipient_user_id = data.get('recipient_user_id')
    recipient_username = data.get('recipient_username')
    
    if not recipient_user_id:
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")
        await state.clear()
        return
    
    # Сохраняем сообщение в базу данных
    message_data = {
        "recipient_user_id": recipient_user_id,
        "sender_user_id": message.from_user.id,
        "message_text": message.text,
        "timestamp": datetime.utcnow(),
        "is_read": False
    }
    
    await messages_collection.insert_one(message_data)
    
    # Отправляем сообщение получателю
    try:
        await message.bot.send_message(
            chat_id=recipient_user_id,
            text=f"📨 Вам пришло анонимное сообщение:\n\n{message.text}"
        )
        await message.answer("✅ Сообщение успешно отправлено!")
    except Exception as e:
        await message.answer("❌ Не удалось доставить сообщение. Возможно, пользователь заблокировал бота.")
    
    await state.clear()

@router.callback_query(F.data == "start_rating")
async def start_rating_process(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipient_username = data.get('recipient_username')
    
    await state.update_data(ratings={})
    await state.set_state(InteractionStates.rating_appearance)
    
    # Начинаем с оценки внешности
    keyboard_buttons = []
    for i in range(1, 11):
        keyboard_buttons.append([InlineKeyboardButton(text=f"{i}", callback_data=f"appearance_{i}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback_query.message.edit_text(
        f"Оценка пользователя: @{recipient_username}\n\n"
        f"😍 Оцените внешность (1-10):",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("appearance_"))
async def handle_appearance_rating(callback_query: CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.replace("appearance_", ""))
    
    data = await state.get_data()
    data['ratings']['appearance'] = rating
    await state.update_data(ratings=data['ratings'])
    await state.set_state(InteractionStates.rating_character)
    
    # Переходим к оценке характера
    keyboard_buttons = []
    for i in range(1, 11):
        keyboard_buttons.append([InlineKeyboardButton(text=f"{i}", callback_data=f"character_{i}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {rating}/10 ✅\n\n"
        f"👏 Оцените характер (1-10):",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("character_"))
async def handle_character_rating(callback_query: CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.replace("character_", ""))
    
    data = await state.get_data()
    data['ratings']['character'] = rating
    await state.update_data(ratings=data['ratings'])
    await state.set_state(InteractionStates.rating_intelligence)
    
    ratings = data['ratings']
    
    keyboard_buttons = []
    for i in range(1, 11):
        keyboard_buttons.append([InlineKeyboardButton(text=f"{i}", callback_data=f"intelligence_{i}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {ratings['appearance']}/10 ✅\n"
        f"👏 Характер: {rating}/10 ✅\n\n"
        f"🧠 Оцените ум (1-10):",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("intelligence_"))
async def handle_intelligence_rating(callback_query: CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.replace("intelligence_", ""))
    
    data = await state.get_data()
    data['ratings']['intelligence'] = rating
    await state.update_data(ratings=data['ratings'])
    await state.set_state(InteractionStates.rating_humor)
    
    ratings = data['ratings']
    
    keyboard_buttons = []
    for i in range(1, 11):
        keyboard_buttons.append([InlineKeyboardButton(text=f"{i}", callback_data=f"humor_{i}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {ratings['appearance']}/10 ✅\n"
        f"👏 Характер: {ratings['character']}/10 ✅\n"
        f"🧠 Ум: {rating}/10 ✅\n\n"
        f"😂 Оцените чувство юмора (1-10):",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("humor_"))
async def handle_humor_rating(callback_query: CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.replace("humor_", ""))
    
    data = await state.get_data()
    data['ratings']['humor'] = rating
    await state.update_data(ratings=data['ratings'])
    await state.set_state(InteractionStates.rating_trust)
    
    ratings = data['ratings']
    
    keyboard_buttons = []
    for i in range(1, 11):
        keyboard_buttons.append([InlineKeyboardButton(text=f"{i}", callback_data=f"trust_{i}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {ratings['appearance']}/10 ✅\n"
        f"👏 Характер: {ratings['character']}/10 ✅\n"
        f"🧠 Ум: {ratings['intelligence']}/10 ✅\n"
        f"😂 Чувство юмора: {rating}/10 ✅\n\n"
        f"🍬 Оцените уровень доверия (1-10):",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("trust_"))
async def handle_trust_rating(callback_query: CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.replace("trust_", ""))
    
    data = await state.get_data()
    data['ratings']['trust'] = rating
    await state.update_data(ratings=data['ratings'])
    await state.set_state(InteractionStates.wants_relationship)
    
    ratings = data['ratings']
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="relationship_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="relationship_no")]
    ])
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {ratings['appearance']}/10 ✅\n"
        f"👏 Характер: {ratings['character']}/10 ✅\n"
        f"🧠 Ум: {ratings['intelligence']}/10 ✅\n"
        f"😂 Чувство юмора: {ratings['humor']}/10 ✅\n"
        f"🍬 Уровень доверия: {rating}/10 ✅\n\n"
        f"👩‍❤️‍👨 Хотели бы встречаться с этим человеком?",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("relationship_"))
async def handle_relationship_question(callback_query: CallbackQuery, state: FSMContext):
    answer = callback_query.data.replace("relationship_", "")
    
    data = await state.get_data()
    data['wants_relationship'] = answer
    await state.update_data(wants_relationship=answer)
    await state.set_state(InteractionStates.knows_personally)
    
    ratings = data['ratings']
    relationship_text = "Да" if answer == "yes" else "Нет"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="knows_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="knows_no")]
    ])
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {ratings['appearance']}/10 ✅\n"
        f"👏 Характер: {ratings['character']}/10 ✅\n"
        f"🧠 Ум: {ratings['intelligence']}/10 ✅\n"
        f"😂 Чувство юмора: {ratings['humor']}/10 ✅\n"
        f"🍬 Уровень доверия: {ratings['trust']}/10 ✅\n"
        f"👩‍❤️‍👨 Хочет встречаться: {relationship_text} ✅\n\n"
        f"👀 Знакомы ли вы лично с этим человеком?",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("knows_"))
async def handle_knows_personally(callback_query: CallbackQuery, state: FSMContext):
    answer = callback_query.data.replace("knows_", "")
    
    data = await state.get_data()
    data['knows_personally'] = answer
    await state.update_data(knows_personally=answer)
    await state.set_state(InteractionStates.asking_for_message)
    
    ratings = data['ratings']
    relationship_text = "Да" if data['wants_relationship'] == "yes" else "Нет"
    knows_text = "Да" if answer == "yes" else "Нет"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Да, хочу написать сообщение", callback_data="write_message")],
        [InlineKeyboardButton(text="➡️ Нет, отправить только оценку", callback_data="skip_message")]
    ])
    
    await callback_query.message.edit_text(
        f"😍 Внешность: {ratings['appearance']}/10 ✅\n"
        f"👏 Характер: {ratings['character']}/10 ✅\n"
        f"🧠 Ум: {ratings['intelligence']}/10 ✅\n"
        f"😂 Чувство юмора: {ratings['humor']}/10 ✅\n"
        f"🍬 Уровень доверия: {ratings['trust']}/10 ✅\n"
        f"👩‍❤️‍👨 Хочет встречаться: {relationship_text} ✅\n"
        f"👀 Знакомы лично: {knows_text} ✅\n\n"
        f"💬 Хотите добавить личное сообщение к оценке?",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "write_message")
async def request_rating_message(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(InteractionStates.writing_message)
    await callback_query.message.edit_text(
        "✍️ Напишите ваше сообщение для этого пользователя:\n\n"
        "Отправьте текст сообщения следующим сообщением."
    )

@router.callback_query(F.data == "skip_message")
async def skip_message(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(message=None)
    await choose_anonymity(callback_query, state)

@router.message(InteractionStates.writing_message)
async def handle_message_input(message: Message, state: FSMContext):
    await state.update_data(message=message.text)
    await state.set_state(InteractionStates.choosing_anonymity)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Скрыть мою личность (анонимно)", callback_data="send_anonymous")],
        [InlineKeyboardButton(text="📝 Показать мое имя", callback_data="send_named")]
    ])
    
    await message.answer("Как отправить оценку?", reply_markup=keyboard)

async def choose_anonymity(callback_query: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Скрыть мою личность (анонимно)", callback_data="send_anonymous")],
        [InlineKeyboardButton(text="📝 Показать мое имя", callback_data="send_named")]
    ])
    
    await callback_query.message.edit_text("Как отправить оценку?", reply_markup=keyboard)

@router.callback_query(F.data.startswith("send_"))
async def send_rating(callback_query: CallbackQuery, state: FSMContext):
    anonymity = callback_query.data.replace("send_", "")
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or f"id_{user_id}"
    
    data = await state.get_data()
    target_user_id = data['recipient_user_id']
    target_username = data['recipient_username']
    ratings = data['ratings']
    wants_relationship = data['wants_relationship']
    knows_personally = data['knows_personally']
    message_text = data.get('message')
    
    # Формируем сообщение с оценкой
    sender_name = "👤 Аноним" if anonymity == "anonymous" else f"👤 @{username}"
    relationship_text = "Да" if wants_relationship == "yes" else "Нет"
    knows_text = "Да" if knows_personally == "yes" else "Нет"
    
    rating_message = (
        f"⭐️ Новая оценка!\n"
        f"От кого: {sender_name}\n\n"
        f"😍 Внешность: {ratings['appearance']}/10\n"
        f"👏 Характер: {ratings['character']}/10\n"
        f"🧠 Ум: {ratings['intelligence']}/10\n"
        f"😂 Чувство юмора: {ratings['humor']}/10\n"
        f"🍬 Уровень доверия: {ratings['trust']}/10\n"
        f"👩‍❤️‍👨 Хочет встречаться: {relationship_text}\n"
        f"👀 Знакомы лично: {knows_text}"
    )
    
    if message_text:
        rating_message += f"\n\n💬 Сообщение:\n{message_text}"
    
    # Сохраняем оценку в базу данных
    rating_record = {
        "from_user_id": user_id,
        "to_user_id": target_user_id,
        "anonymous": anonymity == "anonymous",
        "ratings": ratings,
        "wants_relationship": wants_relationship == "yes",
        "knows_personally": knows_personally == "yes",
        "message": message_text,
        "timestamp": datetime.utcnow()
    }
    
    await ratings_collection.insert_one(rating_record)
    
    # Отправляем оценку получателю
    try:
        await callback_query.bot.send_message(
            chat_id=target_user_id,
            text=rating_message
        )
        await callback_query.message.edit_text("✅ Оценка успешно отправлена!")
    except Exception as e:
        await callback_query.message.edit_text("❌ Не удалось отправить оценку. Возможно, пользователь заблокировал бота.")
    
    await state.clear()

@router.message(F.text == "/start")
async def start_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"id_{user_id}"
    
    existing_user = await users_collection.find_one({"user_id": user_id})
    if not existing_user:
        link_id = str(uuid4())
        await users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "link_id": link_id,
            "ratings": [],
            "created_at": datetime.utcnow()
        })
    else:
        link_id = existing_user["link_id"]
    
    bot_username = (await message.bot.me()).username
    link = f"https://t.me/{bot_username}?start=send_{link_id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Моя ссылка", url=link)],
        [InlineKeyboardButton(text="📊 Мои сообщения", callback_data="my_messages")],
        [InlineKeyboardButton(text="📈 Мои оценки", callback_data="my_ratings")]
    ])
    
    await message.answer(
        "👋 Добро пожаловать в бота анонимных сообщений и оценок!\n\n"
        f"🔗 Ваша ссылка:\n{link}\n\n"
        "📝 Поделитесь этой ссылкой с друзьями, чтобы получать анонимные сообщения и оценки!\n\n"
        "✨ По вашей ссылке люди смогут:\n"
        "• Оценить вас по различным критериям\n"
        "• Отправить анонимное сообщение\n"
        "• Выбрать, показывать ли свое имя или остаться анонимом",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "my_messages")
async def show_my_messages(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    messages_cursor = messages_collection.find(
        {"recipient_user_id": user_id}
    ).sort("timestamp", -1).limit(10)
    
    messages_list = await messages_cursor.to_list(length=10)
    
    if not messages_list:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
        ])
        await callback_query.message.edit_text("📭 У вас пока нет сообщений.", reply_markup=keyboard)
        return
    
    text = "📨 Ваши последние сообщения:\n\n"
    for i, msg in enumerate(messages_list, 1):
        timestamp = msg['timestamp'].strftime("%d.%m.%Y %H:%M")
        preview = msg['message_text'][:50] + "..." if len(msg['message_text']) > 50 else msg['message_text']
        text += f"{i}. {timestamp}\n{preview}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "my_ratings")
async def show_my_ratings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем последние оценки пользователя
    ratings_cursor = ratings_collection.find(
        {"to_user_id": user_id}
    ).sort("timestamp", -1).limit(5)
    
    ratings_list = await ratings_cursor.to_list(length=5)
    
    if not ratings_list:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
        ])
        await callback_query.message.edit_text("📊 У вас пока нет оценок.", reply_markup=keyboard)
        return
    
    text = "📊 Ваши последние оценки:\n\n"
    
    for i, rating in enumerate(ratings_list, 1):
        sender_name = "Аноним" if rating['anonymous'] else f"@{rating.get('from_username', 'Unknown')}"
        timestamp = rating['timestamp'].strftime("%d.%m.%Y %H:%M")
        
        text += f"{i}. От: {sender_name} ({timestamp})\n"
        text += f"   😍 Внешность: {rating['ratings']['appearance']}/10\n"
        text += f"   👏 Характер: {rating['ratings']['character']}/10\n"
        text += f"   🧠 Ум: {rating['ratings']['intelligence']}/10\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    if not user:
        await callback_query.answer("Ошибка: пользователь не найден")
        return
    
    bot_username = (await callback_query.bot.me()).username
    link = f"https://t.me/{bot_username}?start=send_{user['link_id']}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Моя ссылка", url=link)],
        [InlineKeyboardButton(text="📊 Мои сообщения", callback_data="my_messages")],
        [InlineKeyboardButton(text="📈 Мои оценки", callback_data="my_ratings")]
    ])
    
    await callback_query.message.edit_text(
        "👋 Добро пожаловать в бота анонимных сообщений и оценок!\n\n"
        f"🔗 Ваша ссылка:\n{link}\n\n"
        "📝 Поделитесь этой ссылкой с друзьями, чтобы получать анонимные сообщения и оценки!\n\n"
        "✨ По вашей ссылке люди смогут:\n"
        "• Оценить вас по различным критериям\n"
        "• Отправить анонимное сообщение\n"
        "• Выбрать, показывать ли свое имя или остаться анонимом",
        reply_markup=keyboard
    )