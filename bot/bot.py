import logging
import os
import sys
from typing import Text

import alpha_vantage.timeseries as alpha_vantage
import redis
import telegram.ext as telegram

import storage

_I18N = {
    "greeting_message": {
        "en": "Hello. I am your personal accountant. I am happy to track all of your expenses.",
        "ru": "Привет. Я - ваш персональных бухгалтер. Я рад следить за всеми вашими расходами."
    },
    "do_not_understand": {
        "en": "Sorry, I don't understand you.",
        "ru": "Простите, я вас не понимаю."
    },
    "clarify_symbol": {
        "en": "Which symbol are you interested in?",
        "ru": "Цену какой акции вы хотите узнать?"
    },
    "unknown_symbol": {
        "en": "Sorry, the symbol is unknown. Please specify correct symbol.",
        "ru": "Простите, код акции не найден. Укажите правильный код акции.",
    }
}


class State:
    """State class contains possible FSM states."""
    START_STATE = "start"
    CLARIFY_SYMBOL = 'clarify symbol'


class StateKeeper(redis.Redis):
    def __getitem__(self, user_id):
        state = self.get(user_id)
        if not state:
            self.set(user_id, State.START_STATE)
            return State.START_STATE
        return state

    def __setitem__(self, user_id, state):
        return self.set(user_id, state)


class FinanceBot:
    def __init__(self, telegram_api_token: Text, alpha_vantage_api_token: Text,
                 redis_address: Text = "localhost", path_to_db: Text = "db/"):
        self.bot = telegram.Updater(token=telegram_api_token, use_context=True)
        self.stock_api = alpha_vantage.TimeSeries(alpha_vantage_api_token)
        self.state = StateKeeper(host=redis_address, decode_responses=True)
        self.storage = storage.Storage(path_to_db)

    def dispatch(self):
        dispatcher = self.bot.dispatcher
        dispatcher.add_handler(telegram.CommandHandler(
            "start", self.handler_start))

    def handler_start(self, update, context):
        chat_id = update.effective_chat.id
        lang = update.effective_user.language_code or "en"
        context.bot.send_message(
            chat_id=chat_id, text=_I18N["greeting_message"][lang])

    def start_polling(self):
        self.dispatch()
        self.bot.start_polling()
        self.bot.idle()


def main():
    telegram_bot_api_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    alpha_vantage_api_token = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not alpha_vantage_api_token:
        sys.exit(
            "Alpha Vantage API token not found in ENV variables. Please set ALPHAVANTAGE_API_KEY env variable.")
    if not telegram_bot_api_token:
        sys.exit(
            "Telegram Bot token not found in ENV variables. Please set TELEGRAM_BOT_TOKEN env variable.")

    logging_level = logging.WARNING
    if os.environ.get("env") == "dev":
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level)

    bot = FinanceBot(telegram_bot_api_token, alpha_vantage_api_token)
    bot.start_polling()


if __name__ == "__main__":
    main()
