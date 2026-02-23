
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from states import GameStates
import random
import asyncio
from datetime import datetime, timedelta
from config import CHANNEL_ID, ADMINS, CRYPTO_PAY_TOKEN
from database import db
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.invoice import Invoice
from keyboards import (
    get_main_menu_kb, get_profile_kb, get_referral_kb, 
    get_bonus_spin_kb, get_top_players_kb, get_play_kb,
    get_tg_games_kb, get_author_games_kb,
    get_darts_kb, get_dice_kb, get_bowling_kb,
    get_football_kb, get_basketball_kb,
    get_dice_2rolls_kb, get_dice_3rolls_kb,
    get_dice_exact_double_kb, get_dice_exact_triple_kb,
    get_deposit_method_kb, get_deposit_amounts_kb,
    get_withdraw_method_kb, get_withdraw_currency_kb
)

router = Router()
crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)

@router.message(Command("givebalance"))
async def cmd_give_balance(message: Message, command: CommandObject):
    # Проверка на админа
    if message.from_user.id not in ADMINS:
        return

    # Проверка аргументов
    if not command.args:
        await message.answer("❌ Используйте: <code>/givebalance ID сумма</code>")
        return

    args = command.args.split()
    if len(args) != 2:
        await message.answer("❌ Неверное количество аргументов. Используйте: <code>/givebalance ID сумма</code>")
        return

    try:
        target_id = int(args[0])
        amount = float(args[1].replace(",", "."))
    except ValueError:
        await message.answer("❌ ID должен быть числом, а сумма — числом или десятичной дробью.")
        return

    # Проверяем, существует ли пользователь
    user = db.get_user(target_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID <code>{target_id}</code> не найден в базе данных.")
        return

    # Обновляем баланс
    if db.update_balance(target_id, amount):
        await message.answer(f"✅ Баланс пользователя <code>{target_id}</code> успешно изменен на <b>{amount:.2f}$</b>")
        
        # Уведомляем пользователя
        try:
            await message.bot.send_message(target_id, f"💰 Ваш баланс был {'пополнен' if amount > 0 else 'изменен'} администратором на <b>{amount:.2f}$</b>")
        except:
            pass # Если бот заблокирован пользователем
    else:
        await message.answer(f"❌ Не удалось изменить баланс (возможно, недостаточно средств для списания).")

@router.callback_query(F.data.startswith("auth_game_"))
async def process_auth_game_click(callback: CallbackQuery, state: FSMContext):
    game_data = callback.data.split("_")
    multiplier = game_data[2].replace("x", "") # Например "2"
    
    # Маппинг названий и эмодзи
    game_info = {
        "x2": ("🧭", "Компас"),
        "x3": ("🐟", "Рыбка"),
        "x5": ("🎈", "Шарик"),
        "x10": ("💣", "Бомбочка"),
        "x20": ("🎮", "Консоль"),
        "x30": ("🦋", "Бабочка"),
        "x50": ("🚀", "Ракета"),
        "x100": ("🐳", "Кит")
    }
    
    emoji, name = game_info.get(f"x{multiplier}", ("🎮", "Игра"))
    user_data = db.get_user(callback.from_user.id)
    balance = user_data[3] if user_data else 0.0
    
    await state.update_data(
        game_multiplier=float(multiplier), 
        game_emoji=emoji, 
        game_name=name,
        is_tg_game=False
    )
    await state.set_state(GameStates.waiting_for_bet_amount)
    
    text = (
        f"{emoji} <b>{name}</b>\n\n"
        f"<i>Пришлите сумму ставки в долларах</i>\n\n"
        f"💵 <b>Баланс бота: {balance:.2f}$</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="< Изменить игру", callback_data="author_games"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.message(GameStates.waiting_for_bet_amount)
async def handle_bet_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        return # Игнорируем некорректный ввод
        
    if amount < 0.1:
        await message.answer("❌ Минимальная сумма ставки — 0.10$")
        return
        
    user_data = db.get_user(message.from_user.id)
    balance = user_data[3] if user_data else 0.0
    
    if amount > balance:
        await message.answer(f"❌ Недостаточно средств! Ваш баланс: {balance:.2f}$")
        return
        
    data = await state.get_data()
    multiplier = data.get("game_multiplier")
    emoji = data.get("game_emoji")
    name = data.get("game_name")
    
    # Списываем ставку атомарно
    if not db.update_balance(message.from_user.id, -amount):
        await message.answer(f"❌ Недостаточно средств! Ваш баланс: {balance:.2f}$")
        await state.clear()
        return

    # Очищаем состояние сразу, чтобы избежать повторных ставок во время анимации
    await state.clear()

    wait_msg = None

    # Дизайн сообщения о ставке
    bet_announcement = (
        f"<b>{message.from_user.full_name}</b> ставит <b>{amount:.2f}</b> 💵\n\n"
        f"{emoji} <b>{name}</b>\n"
        f"Множитель должен выпасть <b>x{multiplier}</b>\n\n"
        f"🤞 <b>Желаем удачи!</b>"
    )

    play_mode = user_data[12] if user_data and len(user_data) > 12 else "bot"
    bot_link = f"https://t.me/{(await message.bot.get_me()).username}"
    
    target_chat = CHANNEL_ID if play_mode == "channel" else message.chat.id

    if play_mode == "channel":
        try:
            channel_kb = InlineKeyboardBuilder()
            channel_kb.row(InlineKeyboardButton(text="Сделать ставку ↗️", url=bot_link))
            await message.bot.send_message(
                CHANNEL_ID, 
                bet_announcement, 
                reply_markup=channel_kb.as_markup(),
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        except Exception:
            pass
    else:
        wait_msg = await message.answer(bet_announcement)
    
    # Отправляем анимацию игры
    is_tg_game = data.get("is_tg_game")
    game_type = data.get("game_type")
    outcome_key = data.get("outcome_key")

    user_id = message.from_user.id
    if is_tg_game:
        # Нормализуем эмодзи для answer_dice
        dice_emoji = emoji.replace("️", "") # Удаляем variation selector
        
        # Проверка на многократные броски
        multi_roll_keywords = ["2rolls", "both", "double", "product_18", "3rolls", "three", "triple"]
        is_multi_roll = any(kw in outcome_key for kw in multi_roll_keywords)

        if is_multi_roll:
            if any(kw in outcome_key for kw in ["2rolls", "both", "double", "product_18"]):
                d1 = await message.bot.send_dice(target_chat, emoji="🎲")
                await asyncio.sleep(3.5)
                d2 = await message.bot.send_dice(target_chat, emoji="🎲")
                await asyncio.sleep(3.5)
                v1, v2 = d1.dice.value, d2.dice.value
                
                if outcome_key == "2rolls": is_win = (v1 == 6 and v2 == 6)
                elif outcome_key == "both_even": is_win = (v1 % 2 == 0 and v2 % 2 == 0)
                elif outcome_key == "both_odd": is_win = (v1 % 2 != 0 and v2 % 2 != 0)
                elif outcome_key == "both_less": is_win = (v1 <= 3 and v2 <= 3)
                elif outcome_key == "both_more": is_win = (v1 >= 4 and v2 >= 4)
                elif outcome_key == "any_double": is_win = (v1 == v2)
                elif outcome_key == "product_18": is_win = (v1 * v2 >= 18)
                elif outcome_key.startswith("double_"):
                    target = int(outcome_key.split("_")[1])
                    is_win = (v1 == target and v2 == target)
                else: is_win = False
            else: # 3 rolls
                d1 = await message.bot.send_dice(target_chat, emoji="🎲")
                await asyncio.sleep(3.5)
                d2 = await message.bot.send_dice(target_chat, emoji="🎲")
                await asyncio.sleep(3.5)
                d3 = await message.bot.send_dice(target_chat, emoji="🎲")
                await asyncio.sleep(3.5)
                v1, v2, v3 = d1.dice.value, d2.dice.value, d3.dice.value
                
                if outcome_key == "3rolls": is_win = (v1 == 6 and v2 == 6 and v3 == 6)
                elif outcome_key == "three_even": is_win = (v1 % 2 == 0 and v2 % 2 == 0 and v3 % 2 == 0)
                elif outcome_key == "three_odd": is_win = (v1 % 2 != 0 and v2 % 2 != 0 and v3 % 2 != 0)
                elif outcome_key == "three_less": is_win = (v1 <= 3 and v2 <= 3 and v3 <= 3)
                elif outcome_key == "three_more": is_win = (v1 >= 4 and v2 >= 4 and v3 >= 4)
                elif outcome_key == "any_triple": is_win = (v1 == v2 == v3)
                elif outcome_key.startswith("triple_"):
                    target = int(outcome_key.split("_")[1])
                    is_win = (v1 == target and v2 == target and v3 == target)
                else: is_win = False
        else:
            msg = await message.bot.send_dice(target_chat, emoji=dice_emoji)
            await asyncio.sleep(3.5) # Ждем завершения анимации
            val = msg.dice.value
            
            if game_type == "dice":
                if outcome_key == "even": is_win = (val % 2 == 0)
                elif outcome_key == "odd": is_win = (val % 2 != 0)
                elif outcome_key == "less": is_win = (val <= 3)
                elif outcome_key == "more": is_win = (val >= 4)
                elif outcome_key == "ladder": is_win = (val >= 4)
                else: is_win = (str(val) == outcome_key)
            elif game_type == "darts":
                if outcome_key == "center": is_win = (val == 6)
                elif outcome_key == "red": is_win = (val in [2, 4, 6])
                elif outcome_key == "white": is_win = (val in [3, 5])
                elif outcome_key == "miss": is_win = (val == 1)
            elif game_type == "bowling":
                if outcome_key == "strike": is_win = (val == 6)
                elif outcome_key == "miss": is_win = (val == 1)
            elif game_type == "football":
                if outcome_key == "goal": is_win = (val >= 3)
                elif outcome_key == "miss": is_win = (val <= 2)
            elif game_type == "basketball":
                if outcome_key == "clean": is_win = (val == 5)
                elif outcome_key == "any": is_win = (val >= 4)
                elif outcome_key == "stuck": is_win = (val == 3)
                elif outcome_key == "miss": is_win = (val <= 2)
            else:
                is_win = False
    else:
        # Авторские игры - используем старую логику (эмодзи + рандом)
        await message.bot.send_message(target_chat, emoji)
        await asyncio.sleep(1.0)
        
        chances = {
            1.65: 0.55, 2.0: 0.40, 2.2: 0.38, 2.5: 0.30, 3.0: 0.28,
            5.0: 0.18, 6.0: 0.14, 10.0: 0.10, 20.0: 0.05, 30.0: 0.04,
            36.0: 0.02, 50.0: 0.03, 100.0: 0.01, 150.0: 0.005
        }
        win_chance = chances.get(multiplier, (1 / multiplier) * 0.9)
        is_win = random.random() < win_chance
    
    game_emojis = {
        "dice": "🎲",
        "football": "⚽️",
        "basketball": "🏀",
        "darts": "🎯",
        "bowling": "🎳"
    }
    game_emoji = game_emojis.get(game_type, "🎮")

    if is_win:
        win_amount = round(amount * multiplier, 2)
        db.update_balance(user_id, win_amount)
        db.update_turnover(user_id, amount)
        
        result_text = (
            f"<b>🎉 Поздравляем, {message.from_user.first_name}! Вы выиграли {win_amount:.2f} 💵</b>\n\n"
            f"<b>💸 Выигрыш зачислен на баланс <a href='{bot_link}'>бота</a></b>"
        )
    else:
        db.update_turnover(user_id, amount)
        # Если есть пригласитель, начисляем ему 5% от проигрыша
        referrer_id = user_data[10] if user_data and len(user_data) > 10 else None
        if referrer_id:
            ref_bonus = round(amount * 0.05, 2)
            db.update_ref_balance(referrer_id, ref_bonus)
            
        result_text = (
            f"<b>😔 К сожалению, ставка \"{message.from_user.first_name}\" не сыграла.</b>\n\n"
            f"<b>🍀 Желаем удачи в следующих ставках!</b>"
        )

    if wait_msg:
        try:
            await wait_msg.delete()
        except:
            pass
    
    if play_mode == "channel":
        try:
            channel_kb = InlineKeyboardBuilder()
            channel_kb.row(InlineKeyboardButton(text="Сделать ставку ↗️", url=bot_link))
            await message.bot.send_message(
                CHANNEL_ID, 
                result_text, 
                reply_markup=channel_kb.as_markup(), 
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        except Exception as e:
            # Логируем ошибку, но не отправляем в ЛС, если выбран режим канала
            print(f"Error sending to channel: {e}")
    else:
        await message.answer(result_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
    
@router.message(Command("reserve"))
async def cmd_reserve(message: Message):
    try:
        # Получаем реальные балансы из Crypto Pay
        balances = await crypto.get_balance()
        
        # Список интересующих нас валют
        assets_to_show = ["USDT", "TON", "TRX"]
        
        total_usd = 0.0
        details_text = ""
        
        # Получаем курсы валют для расчета общего резерва в USD
        exchange_rates = await crypto.get_exchange_rates()
        
        for asset_balance in balances:
            # В библиотеке aiocryptopay поле называется currency или asset
            # Проверяем атрибут динамически
            asset_name = getattr(asset_balance, "currency", getattr(asset_balance, "asset", None))
            
            if asset_name in assets_to_show:
                amount = asset_balance.available
                
                # Ищем курс к USD
                rate = 1.0
                if asset_name != "USDT":
                    # Ищем пару ASSET/USD
                    rate_obj = next((r for r in exchange_rates if r.source == asset_name and r.target == "USD"), None)
                    if rate_obj:
                        rate = rate_obj.rate
                
                asset_usd = amount * rate
                total_usd += asset_usd
                
                details_text += f"{asset_name}: {amount:,.2f} ({asset_usd:,.2f}$)\n"
        
        text = (
            f"🏦 <b>Резерв казино: ${total_usd:,.2f}</b>\n\n"
            f"<blockquote>"
            f"🦋 <b>Crypto Bot: {total_usd:,.2f}$</b>\n\n"
            f"{details_text}"
            f"</blockquote>\n"
            f"🔎 <b>В резерве – только реальные деньги, готовые к моментальному выводу. Все прозрачно и честно, никаких задержек!</b>"
        )
        await message.answer(text)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении данных резерва: {e}")

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Получаем информацию о боте
    bot_info = await message.bot.get_me()
    bot_name = bot_info.first_name
    
    # Обработка реферального кода
    referrer_id = None
    if command.args:
        try:
            # Поддержка как просто ID, так и ID с префиксом (например U123)
            ref_str = command.args
            if ref_str.startswith("U"):
                ref_str = ref_str[1:]
            referrer_id = int(ref_str)
            
            # Нельзя пригласить самого себя
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            referrer_id = None

    # Регистрируем пользователя в БД
    is_new_user = db.add_user(user_id, username, full_name, referrer_id)
    
    # Если это новый пользователь и у него есть пригласитель
    if is_new_user and referrer_id:
        try:
            # Начисляем 2 спина пригласителю
            db.update_bonus_spins(referrer_id, 2)
            # Уведомляем пригласителя
            await message.bot.send_message(
                referrer_id, 
                f"🎉 По вашей ссылке зарегистрировался новый игрок <b>{full_name}</b>!\n🎁 Вам начислено <b>2 бонусных спина</b>!"
            )
        except Exception:
            pass # Если бот заблокирован у пригласителя

    text = (
        f"🔥 <b>Добро пожаловать, {full_name}!</b>\n\n"
        f"🚀 <b>Канал где публикуются ставки, акции, новости</b> - t.me/cdeltabet\n\n"
        f"💸 <b>Забирай 10% кешбек в начале каждого месяца, если ваша игровая статистика оказалась отрицательная. Кешбек приходит в рассылке!</b>\n\n"
        f"<blockquote>Пока ты думаешь, кто-то уже берёт джекпот! 🎰</blockquote>"
    )
    
    # ОДНО СООБЩЕНИЕ: Текст + Inline кнопки
    await message.answer(
        text, 
        reply_markup=get_main_menu_kb(), 
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@router.callback_query(F.data.startswith("play_mode_"))
async def process_play_mode(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[2] # bot or channel
    db.update_play_mode(callback.from_user.id, mode)
    
    mode_text = "🤖 В боте" if mode == "bot" else "💎 В канале"
    await callback.answer(f"✅ Режим игры изменен: {mode_text}")
    
    # Обновляем клавиатуру
    text = (
        "🎮 <b>Выберите игру, на которую хотите сделать ставку!</b>\n\n"
        "🔒 <b>Итог каждой игры приходит с серверов Telegram – это гарантирует прозрачность и честность! Резерв бота /reserve.</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_play_kb(mode))

@router.callback_query(F.data == "play")
async def show_play_menu(callback: CallbackQuery, state: FSMContext):
    user_data = db.get_user(callback.from_user.id)
    play_mode = user_data[12] if user_data and len(user_data) > 12 else "bot"
        
    text = (
        "🎮 <b>Выберите игру, на которую хотите сделать ставку!</b>\n\n"
        "🔒 <b>Итог каждой игры приходит с серверов Telegram – это гарантирует прозрачность и честность! Резерв бота /reserve.</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_play_kb(play_mode))

@router.callback_query(F.data == "tg_games")
async def show_tg_games(callback: CallbackQuery):
    text = (
        "🎮 <b>Выберите Telegram игру</b>\n\n"
        "🔻 Широкий выбор исходов для точных и прибыльных ставок!"
    )
    await callback.message.edit_text(text, reply_markup=get_tg_games_kb())

@router.callback_query(F.data == "game_dice_bet")
async def show_dice_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎲 <b>Выберите исход игры!</b>", reply_markup=get_dice_kb())

@router.callback_query(F.data == "dice_2rolls_menu")
async def show_dice_2rolls_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎲 <b>Выберите исход игры (2 броска)!</b>", reply_markup=get_dice_2rolls_kb())

@router.callback_query(F.data == "dice_3rolls_menu")
async def show_dice_3rolls_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎲 <b>Выберите исход игры (3 броска)!</b>", reply_markup=get_dice_3rolls_kb())

@router.callback_query(F.data == "dice_exact_double_menu")
async def show_dice_exact_double_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎲 <b>Выберите точный дубль!</b>", reply_markup=get_dice_exact_double_kb())

@router.callback_query(F.data == "dice_exact_triple_menu")
async def show_dice_exact_triple_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎲 <b>Выберите точный трипл!</b>", reply_markup=get_dice_exact_triple_kb())

@router.callback_query(F.data == "game_football_bet")
async def show_football_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("⚽️ <b>Выберите исход игры!</b>", reply_markup=get_football_kb())

@router.callback_query(F.data == "game_basketball_bet")
async def show_basketball_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🏀 <b>Выберите исход игры!</b>", reply_markup=get_basketball_kb())

@router.callback_query(F.data == "game_darts_bet")
async def show_darts_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎯 <b>Выберите исход игры!</b>", reply_markup=get_darts_kb())

@router.callback_query(F.data == "game_bowling_bet")
async def show_bowling_outcomes(callback: CallbackQuery):
    await callback.message.edit_text("🎳 <b>Выберите исход игры!</b>", reply_markup=get_bowling_kb())

@router.callback_query(F.data.startswith("tg_"))
async def process_tg_game_click(callback: CallbackQuery, state: FSMContext):
    # Формат: tg_game_multiplier_outcome
    # Например: tg_darts_x6_center или tg_dice_x3.5_both_even
    data = callback.data.split("_")
    game_type = data[1]
    multiplier = float(data[2].replace("x", ""))
    # Собираем остаток обратно в outcome_key, так как там могут быть подчеркивания
    outcome_key = "_".join(data[3:])
    
    game_emojis = {
        "darts": "🎯",
        "dice": "🎲",
        "bowling": "🎳",
        "football": "⚽️",
        "basketball": "🏀"
    }
    
    outcome_names = {
        "center": "Прямо в центр",
        "red": "Красный сектор",
        "white": "Белый сектор",
        "miss": "Промах/Отскок",
        "2rolls": "2 Броска",
        "3rolls": "3 Броска",
        "both_even": "Оба чётных",
        "both_odd": "Оба нечёт",
        "both_less": "Оба меньше",
        "both_more": "Оба больше",
        "any_double": "Любой дубль",
        "product_18": "Произведения 18+",
        "double_1": "Дубль 1", "double_2": "Дубль 2", "double_3": "Дубль 3",
        "double_4": "Дубль 4", "double_5": "Дубль 5", "double_6": "Дубль 6",
        "three_even": "Три чётных",
        "three_odd": "Три нечёт",
        "three_less": "Меньше (три)",
        "three_more": "Больше (три)",
        "any_triple": "Любой трипл",
        "triple_1": "Трипл 1", "triple_2": "Трипл 2", "triple_3": "Трипл 3",
        "triple_4": "Трипл 4", "triple_5": "Трипл 5", "triple_6": "Трипл 6",
        "even": "Чёт",
        "odd": "Нечёт",
        "less": "Меньше",
        "more": "Больше",
        "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6",
        "ladder": "Лесенка",
        "strike": "Страйк",
        "goal": "Гол",
        "clean": "Чистый гол",
        "any": "Любой гол",
        "stuck": "Застрял мяч"
    }
    
    emoji = game_emojis.get(game_type, "🎮")
    name = outcome_names.get(outcome_key, outcome_key)
    
    user_data = db.get_user(callback.from_user.id)
    balance = user_data[3] if user_data else 0.0
    
    await state.update_data(
        game_multiplier=multiplier,
        game_emoji=emoji,
        game_name=name,
        game_type=game_type,
        outcome_key=outcome_key,
        is_tg_game=True
    )
    await state.set_state(GameStates.waiting_for_bet_amount)
    
    text = (
        f"{emoji} <b>{name} (x{multiplier})</b>\n\n"
        f"<i>Пришлите сумму ставки в долларах</i>\n\n"
        f"💵 <b>Баланс бота: {balance:.2f}$</b>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="< Назад", callback_data=f"game_{game_type}_bet"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "author_games")
async def show_author_games(callback: CallbackQuery):
    text = (
        "👾 <b>Выберите авторскую игру!</b>\n\n"
        "🔻 В этих играх система генерирует число: чем выше множитель, тем шире диапазон и сложнее победа."
    )
    await callback.message.edit_text(text, reply_markup=get_author_games_kb())

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    full_name = callback.from_user.full_name
    text = (
        f"🔥 <b>Добро пожаловать, {full_name}!</b>\n\n"
        f"🚀 <b>Канал где публикуются ставки, акции, новости</b> - t.me/CDeltaBet\n\n"
        f"💸 <b>Забирай 10% кешбек в начале каждого месяца, если ваша игровая статистика оказалась отрицательная. Кешбек приходит в рассылке!</b>\n\n"
        f"<blockquote>Пока ты думаешь, кто-то уже берёт джекпот! 🎰</blockquote>"
    )
    await callback.message.edit_text(
        text, 
        reply_markup=get_main_menu_kb(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    
    if not user_data:
        # На случай если БД пустая или сбой
        db.add_user(callback.from_user.id, callback.from_user.username, callback.from_user.full_name)
        user_data = db.get_user(callback.from_user.id)

    # Распаковка данных из БД
    # 0: user_id, 1: username, 2: full_name, 3: balance, 4: turnover, 5: reg_date, 6: deposits, 7: withdrawals, 8: bonus_spins, 9: last_bonus_date, 10: referrer_id
    user_id, username, full_name, balance, turnover, reg_date, deposits, withdrawals, *others = user_data
    
    text = (
        f"👤 <b>Имя:</b> {full_name}\n"
        f"ℹ️ <b>Ваш ID:</b> <code>{user_id}</code>\n\n"
        f"💰 <b>Баланс:</b> {balance:.2f}$\n"
        f"📊 <b>Оборот:</b> {turnover:.2f}$\n"
        f"🕒 <b>Дата регистрации:</b> {reg_date}\n\n"
        f"📥 <b>Пополнений:</b> {deposits:.2f}$\n"
        f"📤 <b>Выводов:</b> {withdrawals:.2f}$"
    )
    await callback.message.edit_text(text, reply_markup=get_profile_kb())

@router.callback_query(F.data == "deposit_crypto")
async def show_deposit_methods(callback: CallbackQuery):
    text = "👇 <b>Выберите удобный способ пополнения - средства зачисляются моментально.</b>"
    await callback.message.edit_text(text, reply_markup=get_deposit_method_kb())

@router.callback_query(F.data == "dep_cryptobot")
async def show_cryptobot_deposit(callback: CallbackQuery, state: FSMContext):
    text = (
        "🤖 Пополнение через 🦋 <b>Crypto Bot</b>\n\n"
        "<b>Введите сумму</b> пополнения в USD\n"
        "или выберите сумму из списка!\n\n"
        "Мин сумма: <b>0.10$ - 20000.00$</b>"
    )
    await state.set_state(GameStates.waiting_for_deposit_amount)
    await callback.message.edit_text(text, reply_markup=get_deposit_amounts_kb())

@router.callback_query(F.data.startswith("dep_amt_"))
async def process_deposit_amt_click(callback: CallbackQuery, state: FSMContext):
    amount = float(callback.data.split("_")[2])
    await create_invoice(callback.message, amount, state)

@router.message(GameStates.waiting_for_deposit_amount)
async def handle_deposit_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        return
        
    if amount < 0.1 or amount > 20000:
        await message.answer("❌ Сумма должна быть от 0.10$ до 20000.00$")
        return
        
    await create_invoice(message, amount, state)

async def create_invoice(message: Message, amount: float, state: FSMContext):
    try:
        invoice = await crypto.create_invoice(amount=amount, asset="USDT")
        
        text = (
            f"💸 <b>Сумма пополнения: {amount:.2f}$</b>\n\n"
            f"<b>Нажмите ниже, для оплаты счета!</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Оплатить ↗️", url=invoice.bot_invoice_url))
        builder.row(InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_inv_{invoice.invoice_id}"))
        builder.row(InlineKeyboardButton(text="🔄 Изменить сумму", callback_data="dep_cryptobot"))
        builder.row(InlineKeyboardButton(text="< Назад", callback_data="profile"))
        
        if isinstance(message, Message):
            await message.answer(text, reply_markup=builder.as_markup())
        else: # CallbackQuery.message
            await message.edit_text(text, reply_markup=builder.as_markup())
            
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании счета: {e}")

@router.callback_query(F.data.startswith("check_inv_"))
async def check_invoice_status(callback: CallbackQuery):
    invoice_id = int(callback.data.split("_")[2])
    try:
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        # aiocryptopay возвращает список или один объект в зависимости от версии, проверим оба случая
        invoice = invoices[0] if isinstance(invoices, list) else invoices
        
        if invoice and invoice.status == "paid":
            # Проверяем, не был ли этот счет уже обработан
            if db.is_invoice_processed(invoice_id):
                await callback.answer("❌ Этот счет уже был зачислен", show_alert=True)
                return
                
            amount = invoice.amount
            user_id = callback.from_user.id
            
            # Помечаем как обработанный ПЕРЕД зачислением
            db.mark_invoice_processed(invoice_id)
            
            # Обновляем баланс в БД
            db.update_balance(user_id, amount)
            # Записываем в статистику пополнений
            db.update_deposits(user_id, amount)
            
            await callback.message.edit_text(f"✅ <b>Оплата получена!</b>\n💰 На ваш баланс зачислено <b>{amount:.2f}$</b>")
            
            # Уведомляем админов
            for admin_id in ADMINS:
                try:
                    await callback.bot.send_message(admin_id, f"📥 <b>Новое пополнение!</b>\n👤 Игрок: {callback.from_user.full_name} (ID: {user_id})\n💰 Сумма: {amount:.2f}$")
                except:
                    pass
        else:
            await callback.answer("❌ Оплата еще не поступила", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка проверки: {e}", show_alert=True)

@router.callback_query(F.data == "withdraw_crypto")
async def show_withdraw_methods(callback: CallbackQuery):
    text = "👇 <b>Выберите способ вывода</b>"
    await callback.message.edit_text(text, reply_markup=get_withdraw_method_kb())

@router.callback_query(F.data == "with_cryptobot")
async def show_cryptobot_withdraw(callback: CallbackQuery):
    text = "📤 <b>Выберите валюту для вывода</b>"
    await callback.message.edit_text(text, reply_markup=get_withdraw_currency_kb())

@router.callback_query(F.data.startswith("with_curr_"))
async def process_withdraw_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[2]
    user_data = db.get_user(callback.from_user.id)
    balance = user_data[3] if user_data else 0.0
    
    text = (
        f"🤖 Моментальный вывод в 🦋 <b>Crypto Bot</b>\n\n"
        f"💵 <b>Баланс бота: {balance:.2f}$</b>\n"
        f"<b>Введите сумму</b> вывода в USD\n\n"
        f"Мин сумма: <b>1.10$ - 20000.00$</b>"
    )
    await state.update_data(withdraw_currency=currency)
    await state.set_state(GameStates.waiting_for_withdraw_amount)
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="withdraw_crypto"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.message(GameStates.waiting_for_withdraw_amount)
async def handle_withdraw_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        return
        
    if amount < 1.1 or amount > 20000:
        await message.answer("❌ Сумма должна быть от 1.10$ до 20000.00$")
        return
        
    user_data = db.get_user(message.from_user.id)
    balance = user_data[3] if user_data else 0.0
    
    if amount > balance:
        await message.answer(f"❌ Недостаточно средств! Ваш баланс: {balance:.2f}$")
        return
        
    await state.update_data(withdraw_amount=amount)
    await state.set_state(GameStates.waiting_for_withdraw_address)
    await message.answer("🆔 <b>Введите ваш ID</b> для получения перевода:")

@router.message(GameStates.waiting_for_withdraw_address)
async def handle_withdraw_address(message: Message, state: FSMContext):
    try:
        target_user_id = int(message.text)
    except ValueError:
        await message.answer("❌ ID должен быть числом!")
        return
        
    data = await state.get_data()
    # Очищаем состояние сразу
    await state.clear()
    
    amount = data.get("withdraw_amount")
    currency = data.get("withdraw_currency")
    user_id = message.from_user.id
    
    try:
        # Проверяем баланс приложения (казны)
        me = await crypto.get_me()
        # Проверяем баланс в нужной валюте
        app_balance = await crypto.get_balance()
        # В разных версиях библиотеки поля могут называться asset или currency
        target_balance = next((b for b in app_balance if getattr(b, "currency", getattr(b, "asset", None)) == currency), None)
        
        if not target_balance or target_balance.available < amount:
            await message.answer("❌ Ручной вывод!</b>\nОжидайте!")
            await state.clear()
            return

        # Списываем баланс игрока атомарно
        if not db.update_balance(user_id, -amount):
            await message.answer(f"❌ Недостаточно средств на балансе!")
            await state.clear()
            return
            
        db.update_withdrawals(user_id, amount)
        
        # Отправляем перевод через Crypto Pay (Transfer)
        try:
            transfer = await crypto.transfer(
                user_id=target_user_id,
                asset=currency,
                amount=amount,
                spend_id=f"withdraw_{user_id}_{int(datetime.now().timestamp())}"
            )
            
            await message.answer(f"✅ <b>Выплата успешно отправлена!</b>\n💰 Сумма: <b>{amount:.2f} {currency}</b>\n👤 Получатель ID: <code>{target_user_id}</code>")
            
            # Уведомляем админов
            for admin_id in ADMINS:
                try:
                    await message.bot.send_message(admin_id, f"📤 <b>Новый вывод!</b>\n👤 Игрок: {message.from_user.full_name} (ID: {user_id})\n💰 Сумма: {amount:.2f} {currency}\n🆔 ID получателя: {target_user_id}")
                except:
                    pass
        except Exception as e:
            # В случае ошибки API возвращаем баланс
            db.update_balance(user_id, amount)
            db.update_withdrawals(user_id, -amount)
            await message.answer(f"❌ <b>Ошибка при выводе:</b> {e}\nБаланс возвращен.")
                
    except Exception as e:
        await message.answer(f"❌ <b>Произошла ошибка:</b> {e}")
        
@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    
    # Считаем реальное количество рефералов
    referrals_count = db.get_referrals_count(user_id)
    
    # Получаем информацию о боте динамически
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username
    bot_name = bot_info.first_name
    
    # ref_balance - 11-й элемент (индекс 11) в кортеже из БД
    ref_balance = user_data[11] if user_data and len(user_data) > 11 else 0.0
    
    # В будущем тут можно считать реальный доход из таблицы транзакций
    total_income = ref_balance # Для примера используем текущий реф. баланс
    available_income = ref_balance
    
    text = (
        f"💸 <b>Приглашай друзей и зарабатывай 5% с проигрыша {bot_name}, с каждой ставки!</b> 🎰 <b>За каждого уникального игрока, который прокрутит бесплатно слот – получай 2 бонус спина!</b>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>https://t.me/{bot_username}?start={user_id}</code>\n\n"
        f"🇮🇹 <b>Формула расчета : (Преимущество {bot_name} * игровой оборот / 2) * ставка комиссии 5%</b>\n\n"
        f"<blockquote>(Обновление каждые 5 минут.)</blockquote>\n\n"
        f"👥 <b>Приглашено:</b> {referrals_count}\n"
        f"💰 <b>Доход за все время:</b> {total_income:.2f}$\n"
        f"💸 <b>Доступно на вывод:</b> {available_income:.2f}$"
    )
    await callback.message.edit_text(
        text, 
        reply_markup=get_referral_kb(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@router.callback_query(F.data == "withdraw_profit")
async def withdraw_profit(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    
    ref_balance = round(user_data[11], 2) if user_data and len(user_data) > 11 else 0.0
    
    if ref_balance < 1.0:
        await callback.answer("❌ Минимальная сумма для вывода — 1.00$", show_alert=True)
        return
    
    # Переносим с реф. баланса на основной атомарно
    if not db.update_ref_balance(user_id, -ref_balance):
        await callback.answer("❌ Ошибка при выводе реферального баланса!", show_alert=True)
        return
        
    db.update_balance(user_id, ref_balance)
    
    await callback.answer(f"✅ Успешно выведено {ref_balance:.2f}$ на основной баланс!", show_alert=True)
    
    # Обновляем меню рефералов
    await show_referral(callback)

@router.callback_query(F.data == "referral_list")
async def show_referral_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    referrals = db.get_referrals_list(user_id)
    
    text = "👥 <b>Список ваших приглашенных игроков:</b>\n\n"
    
    if not referrals:
        text += "<i>Вы еще никого не пригласили...</i>"
    else:
        for i, (name,) in enumerate(referrals, 1):
            text += f"{i}. <b>{name}</b>\n"
    
    # Используем простую клавиатуру с кнопкой назад
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="referral"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "bonus_spin")
async def show_bonus_spin(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    # bonus_spins - 8-й элемент (индекс 8) в кортеже из БД
    bonus_spins = user_data[8] if user_data and len(user_data) > 8 else 0
    
    text = (
        f"🎰 <b>Крути слот, выбивай 777 и срывай джекпот! Каждое вращение – шанс на победу! 🎁 Испытай удачу, забери бесплатный спин!</b>\n\n"
        f"🎟 <b>Доступно вращений:</b> {bonus_spins}\n\n"
        f"🎯 <b>Скоро будут добавлены задания, за выполнение которых можно будет получить различные награды. Следите за ботом!</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_bonus_spin_kb())

@router.callback_query(F.data == "spin_slot")
async def spin_slot(callback: CallbackQuery):
    user_data = db.get_user(callback.from_user.id)
    bonus_spins = user_data[8] if user_data and len(user_data) > 8 else 0
    
    if bonus_spins <= 0:
        await callback.answer("❌ У вас нет доступных вращений!", show_alert=True)
        return

    # Уменьшаем количество спинов атомарно
    if not db.update_bonus_spins(callback.from_user.id, -1):
        await callback.answer("❌ У вас нет доступных вращений!", show_alert=True)
        return

    # Отправляем слот
    msg = await callback.message.answer_dice(emoji="🎰")
    
    # Значение 64 в Telegram для 🎰 означает 777
    # Но мы подождем немного для эффекта
    await asyncio.sleep(2) 
    
    if msg.dice.value == 64:
        db.update_balance(callback.from_user.id, 1.0)
        bot_info = await callback.bot.get_me()
        bot_link = f"https://t.me/{bot_info.username}"
        
        win_text = (
            f"<b>🎉 Поздравляем, {callback.from_user.first_name}! Вы выиграли 1.00 💵</b>\n\n"
            f"<b>💸 Выигрыш зачислен на баланс <a href='{bot_link}'>бота</a></b>"
        )
        await callback.message.answer(win_text)
    else:
        loss_text = (
            f"<b>😔 К сожалению, ставка \"{callback.from_user.first_name}\" не сыграла.</b>\n\n"
            f"<b>🍀 Желаем удачи в следующих ставках!</b>"
        )
        await callback.message.answer(loss_text)

    # Обновляем сообщение меню (опционально, можно просто оставить как есть)
    # Но лучше обновить чтобы юзер видел сколько осталось спинов
    user_data = db.get_user(callback.from_user.id)
    bonus_spins = user_data[8]
    text = (
        f"🎰 <b>Крути слот, выбивай 777 и срывай джекпот! Каждое вращение – шанс на победу! 🎁 Испытай удачу, забери бесплатный спин!</b>\n\n"
        f"🎟 <b>Доступно вращений:</b> {bonus_spins}\n\n"
        f"🎯 <b>Скоро будут добавлены задания, за выполнение которых можно будет получить различные награды. Следите за ботом!</b>"
    )
    await callback.message.answer(text, reply_markup=get_bonus_spin_kb())

@router.callback_query(F.data == "get_spin")
async def get_spin(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    
    # last_bonus_date - 9-й элемент (индекс 9)
    last_bonus_str = user_data[9] if user_data and len(user_data) > 9 else None
    
    now = datetime.now()
    
    if last_bonus_str:
        last_bonus_date = datetime.strptime(last_bonus_str, "%Y-%m-%d %H:%M:%S")
        if now < last_bonus_date + timedelta(days=1):
            next_bonus = last_bonus_date + timedelta(days=1)
            remaining = next_bonus - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            await callback.answer(
                f"❌ Бонус уже получен!\nСледующий через: {hours}ч {minutes}м", 
                show_alert=True
            )
            return

    # Выдаем спин и обновляем дату
    db.update_bonus_spins(user_id, 1)
    db.update_last_bonus_date(user_id, now.strftime("%Y-%m-%d %H:%M:%S"))
    
    await callback.answer("✅ Вы получили 1 бонусный спин!", show_alert=True)
    
    # Обновляем меню
    user_data = db.get_user(user_id)
    bonus_spins = user_data[8]
    text = (
        f"🎰 <b>Крути слот, выбивай 777 и срывай джекпот! Каждое вращение – шанс на победу! 🎁 Испытай удачу, забери бесплатный спин!</b>\n\n"
        f"🎟 <b>Доступно вращений:</b> {bonus_spins}\n\n"
        f"🎯 <b>Скоро будут добавлены задания, за выполнение которых можно будет получить различные награды. Следите за ботом!</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_bonus_spin_kb())

@router.callback_query(F.data.startswith("top_"))
async def show_top_players(callback: CallbackQuery):
    period_map = {
        "top_all_time": ("все время", "all_time"),
        "top_today": ("сегодня", "today"),
        "top_yesterday": ("вчера", "yesterday"),
        "top_week": ("неделю", "week"),
        "top_month": ("месяц", "month")
    }
    
    period_name, period_key = period_map.get(callback.data, ("все время", "all_time"))
    
    top_players = db.get_top_players(period_key, 10)
    user_data = db.get_user(callback.from_user.id)
    user_turnover = user_data[4] if user_data else 0.0
    
    text = (
        f"<blockquote>🏆 Топ игроков по обороту за «{period_name}» ❞</blockquote>\n"
        f"<blockquote>(Обновление каждые 5 минут. UTC+0) ❞</blockquote>\n\n"
    )
    
    if not top_players:
        text += "<i>Пока здесь пусто...</i>\n"
    else:
        for i, (name, turnover) in enumerate(top_players, 1):
            text += f"{i}. {name}: <b>{turnover:.2f} $</b>\n"
    
    text += f"\n👤 Ваш оборот: {user_turnover:.2f} $"
    
    await callback.message.edit_text(text, reply_markup=get_top_players_kb(period_key))
