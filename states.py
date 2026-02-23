from aiogram.fsm.state import State, StatesGroup

class GameStates(StatesGroup):
    waiting_for_bet_amount = State()
    waiting_for_deposit_amount = State()
    waiting_for_withdraw_amount = State()
    waiting_for_withdraw_address = State()
