
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎮 Играть", callback_data="play"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
    )
    builder.row(
        InlineKeyboardButton(text="🎰 Бонус спин", callback_data="bonus_spin"),
        InlineKeyboardButton(text="💸 Реф. программа", callback_data="referral")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Топ игроков", callback_data="top_players")
    )
    return builder.as_markup()

def get_profile_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💸 Пополнить", callback_data="deposit_crypto"),
        InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw_crypto")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_deposit_method_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🦋 Crypto Bot", callback_data="dep_cryptobot"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="profile"))
    return builder.as_markup()

def get_deposit_amounts_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1$", callback_data="dep_amt_1"),
        InlineKeyboardButton(text="5$", callback_data="dep_amt_5"),
        InlineKeyboardButton(text="10$", callback_data="dep_amt_10")
    )
    builder.row(
        InlineKeyboardButton(text="25$", callback_data="dep_amt_25"),
        InlineKeyboardButton(text="50$", callback_data="dep_amt_50"),
        InlineKeyboardButton(text="100$", callback_data="dep_amt_100")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="deposit_crypto"))
    return builder.as_markup()

def get_withdraw_method_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🦋 Crypto Bot", callback_data="with_cryptobot"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="profile"))
    return builder.as_markup()

def get_withdraw_currency_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="USDT 🔥", callback_data="with_curr_USDT"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="withdraw_crypto"))
    return builder.as_markup()

def get_top_players_kb(period="all_time"):
    builder = InlineKeyboardBuilder()
    
    # Кнопки периодов
    all_time_text = "• За всё время •" if period == "all_time" else "За всё время"
    today_text = "• За сегодня •" if period == "today" else "За сегодня"
    yesterday_text = "• Вчера •" if period == "yesterday" else "Вчера"
    week_text = "• Неделя •" if period == "week" else "Неделя"
    month_text = "• Месяц •" if period == "month" else "Месяц"
    
    builder.row(
        InlineKeyboardButton(text=all_time_text, callback_data="top_all_time"),
        InlineKeyboardButton(text=today_text, callback_data="top_today")
    )
    builder.row(
        InlineKeyboardButton(text=yesterday_text, callback_data="top_yesterday"),
        InlineKeyboardButton(text=week_text, callback_data="top_week"),
        InlineKeyboardButton(text=month_text, callback_data="top_month")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_referral_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💸 Вывод прибыли", callback_data="withdraw_profit"))
    builder.row(InlineKeyboardButton(text="👥 Список игроков", callback_data="referral_list"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_bonus_spin_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎰 Крутить", callback_data="spin_slot"))
    builder.row(InlineKeyboardButton(text="🎁 Забрать спин", callback_data="get_spin"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="back_to_main"))
    return builder.as_markup()

def get_play_kb(play_mode="bot"):
    builder = InlineKeyboardBuilder()
    
    # Текст кнопок с учетом выбора
    bot_text = "*🤖 Играть в боте*" if play_mode == "bot" else "🤖 Играть в боте"
    channel_text = "*💎 Играть в канале*" if play_mode == "channel" else "💎 Играть в канале"
    
    # Режим игры
    builder.row(
        InlineKeyboardButton(text=bot_text, callback_data="play_mode_bot"),
        InlineKeyboardButton(text=channel_text, callback_data="play_mode_channel")
    )
    # Первый ряд: 5 кнопок с эмодзи игр
    builder.row(
        InlineKeyboardButton(text="🎲", callback_data="game_dice_bet"),
        InlineKeyboardButton(text="⚽️", callback_data="game_football_bet"),
        InlineKeyboardButton(text="🏀", callback_data="game_basketball_bet"),
        InlineKeyboardButton(text="🎯", callback_data="game_darts_bet"),
        InlineKeyboardButton(text="🎳", callback_data="game_bowling_bet")
    )
    # Второй ряд: Telegram игры и Авторские
    builder.row(
        InlineKeyboardButton(text="🎮 Telegram игры", callback_data="tg_games"),
        InlineKeyboardButton(text="👾 Авторские", callback_data="author_games")
    )
    # Четвертый ряд: Назад
    builder.row(
        InlineKeyboardButton(text="< Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_tg_games_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎲 (до x150)", callback_data="game_dice_bet"),
        InlineKeyboardButton(text="⚽️ (до x2.5)", callback_data="game_football_bet"),
        InlineKeyboardButton(text="🏀 (до x5)", callback_data="game_basketball_bet")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 (до x6)", callback_data="game_darts_bet"),
        InlineKeyboardButton(text="🎳 (до x6)", callback_data="game_bowling_bet")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="play"))
    return builder.as_markup()

def get_author_games_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🧭 x2", callback_data="auth_game_x2"),
        InlineKeyboardButton(text="🐟 x3", callback_data="auth_game_x3"),
        InlineKeyboardButton(text="🎈 x5", callback_data="auth_game_x5"),
        InlineKeyboardButton(text="💣 x10", callback_data="auth_game_x10")
    )
    builder.row(
        InlineKeyboardButton(text="🎮 x20", callback_data="auth_game_x20"),
        InlineKeyboardButton(text="🦋 x30", callback_data="auth_game_x30"),
        InlineKeyboardButton(text="🚀 x50", callback_data="auth_game_x50"),
        InlineKeyboardButton(text="🐳 x100", callback_data="auth_game_x100")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="play"))
    return builder.as_markup()

def get_darts_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Прямо в центр (x6)", callback_data="tg_darts_x6_center"),
        InlineKeyboardButton(text="Красный сектор (x2)", callback_data="tg_darts_x2_red")
    )
    builder.row(
        InlineKeyboardButton(text="Белый сектор (x3)", callback_data="tg_darts_x3_white"),
        InlineKeyboardButton(text="Отскок дротика (x6)", callback_data="tg_darts_x6_miss")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="tg_games"))
    return builder.as_markup()

def get_dice_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="2 Броска (до x36)", callback_data="dice_2rolls_menu"),
        InlineKeyboardButton(text="3 Броска (до x150)", callback_data="dice_3rolls_menu")
    )
    builder.row(
        InlineKeyboardButton(text="Чёт (x2)", callback_data="tg_dice_x2_even"),
        InlineKeyboardButton(text="Нечёт (x2)", callback_data="tg_dice_x2_odd")
    )
    builder.row(
        InlineKeyboardButton(text="Меньше (x2)", callback_data="tg_dice_x2_less"),
        InlineKeyboardButton(text="Больше (x2)", callback_data="tg_dice_x2_more")
    )
    builder.row(
        InlineKeyboardButton(text="1 (x6)", callback_data="tg_dice_x6_1"),
        InlineKeyboardButton(text="2 (x6)", callback_data="tg_dice_x6_2"),
        InlineKeyboardButton(text="3 (x6)", callback_data="tg_dice_x6_3")
    )
    builder.row(
        InlineKeyboardButton(text="4 (x6)", callback_data="tg_dice_x6_4"),
        InlineKeyboardButton(text="5 (x6)", callback_data="tg_dice_x6_5"),
        InlineKeyboardButton(text="6 (x6)", callback_data="tg_dice_x6_6")
    )
    builder.row(InlineKeyboardButton(text="Лесенка (x2.2)", callback_data="tg_dice_x2.2_ladder"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="tg_games"))
    return builder.as_markup()

def get_dice_2rolls_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Оба чётных (x3.5)", callback_data="tg_dice_x3.5_both_even"),
        InlineKeyboardButton(text="Оба нечёт (x3.5)", callback_data="tg_dice_x3.5_both_odd")
    )
    builder.row(
        InlineKeyboardButton(text="Оба меньше (x3.5)", callback_data="tg_dice_x3.5_both_less"),
        InlineKeyboardButton(text="Оба больше (x3.5)", callback_data="tg_dice_x3.5_both_more")
    )
    builder.row(InlineKeyboardButton(text="Любой дубль (x5)", callback_data="tg_dice_x5_any_double"))
    builder.row(InlineKeyboardButton(text="Точный дубль (до x36)", callback_data="dice_exact_double_menu"))
    builder.row(InlineKeyboardButton(text="Произведения 18+ (x4.5)", callback_data="tg_dice_x4.5_product_18"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="game_dice_bet"))
    return builder.as_markup()

def get_dice_exact_double_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Дубль 1 (x36)", callback_data="tg_dice_x36_double_1"),
        InlineKeyboardButton(text="Дубль 2 (x36)", callback_data="tg_dice_x36_double_2")
    )
    builder.row(
        InlineKeyboardButton(text="Дубль 3 (x36)", callback_data="tg_dice_x36_double_3"),
        InlineKeyboardButton(text="Дубль 4 (x36)", callback_data="tg_dice_x36_double_4")
    )
    builder.row(
        InlineKeyboardButton(text="Дубль 5 (x36)", callback_data="tg_dice_x36_double_5"),
        InlineKeyboardButton(text="Дубль 6 (x36)", callback_data="tg_dice_x36_double_6")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="dice_2rolls_menu"))
    return builder.as_markup()

def get_dice_3rolls_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Три чётных (x7)", callback_data="tg_dice_x7_three_even"),
        InlineKeyboardButton(text="Три нечёт (x7)", callback_data="tg_dice_x7_three_odd")
    )
    builder.row(
        InlineKeyboardButton(text="Меньше (x7)", callback_data="tg_dice_x7_three_less"),
        InlineKeyboardButton(text="Больше (x7)", callback_data="tg_dice_x7_three_more")
    )
    builder.row(InlineKeyboardButton(text="Любой трипл (x32)", callback_data="tg_dice_x32_any_triple"))
    builder.row(InlineKeyboardButton(text="Точный трипл (до x150)", callback_data="dice_exact_triple_menu"))
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="game_dice_bet"))
    return builder.as_markup()

def get_dice_exact_triple_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Трипл 1 (x150)", callback_data="tg_dice_x150_triple_1"),
        InlineKeyboardButton(text="Трипл 2 (x150)", callback_data="tg_dice_x150_triple_2")
    )
    builder.row(
        InlineKeyboardButton(text="Трипл 3 (x150)", callback_data="tg_dice_x150_triple_3"),
        InlineKeyboardButton(text="Трипл 4 (x150)", callback_data="tg_dice_x150_triple_4")
    )
    builder.row(
        InlineKeyboardButton(text="Трипл 5 (x150)", callback_data="tg_dice_x150_triple_5"),
        InlineKeyboardButton(text="Трипл 6 (x150)", callback_data="tg_dice_x150_triple_6")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="dice_3rolls_menu"))
    return builder.as_markup()

def get_bowling_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Страйк (x6)", callback_data="tg_bowling_x6_strike"),
        InlineKeyboardButton(text="Промах (x6)", callback_data="tg_bowling_x6_miss")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="tg_games"))
    return builder.as_markup()

def get_football_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Гол (x1.65)", callback_data="tg_football_x1.65_goal"),
        InlineKeyboardButton(text="Промах (x2.5)", callback_data="tg_football_x2.5_miss")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="tg_games"))
    return builder.as_markup()

def get_basketball_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Чистый гол (x5)", callback_data="tg_basketball_x5_clean"),
        InlineKeyboardButton(text="Любой гол (x2.5)", callback_data="tg_basketball_x2.5_any")
    )
    builder.row(
        InlineKeyboardButton(text="Застрял мяч (x5)", callback_data="tg_basketball_x5_stuck"),
        InlineKeyboardButton(text="Промах (x1.65)", callback_data="tg_basketball_x1.65_miss")
    )
    builder.row(InlineKeyboardButton(text="< Назад", callback_data="tg_games"))
    return builder.as_markup()
