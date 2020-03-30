import os
import re
import sys
from typing import Text

import alpha_vantage.timeseries as alpha_vantage
import redis
import telebot

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


_ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
_TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


class State:
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


# @bot.message_handler(func=lambda message: states[message.from_user.id] == _START_STATE)
# def main_handler(message):
#     lang = message.from_user.language_code or 'en'
#     user_id = message.from_user.id
#     message_text = message.text.lower()

#     if message_text == "/start":
#         bot.send_message(message.chat.id, _I18N['greeting_message'][lang])
#     elif "stock price" in message_text:
#         states[user_id] = _CLARIFY_SYMBOL
#         bot.send_message(message.chat.id, _I18N['clarify_symbol'][lang])
#     else:
#         bot.send_message(message.chat.id, _I18N['do_not_understand'][lang])


# @bot.message_handler(func=lambda message: states[message.from_user.id] == _CLARIFY_SYMBOL)
# def get_quote_handler(message):
#     lang = message.from_user.language_code or 'en'
#     user_id = message.from_user.id
#     message_text = message.text.lower()

#     symbol_info = None
#     try:
#         bot.send_chat_action(message.chat.id, "typing")
#         symbol_info, _ = stock_api.get_quote_endpoint(message_text)
#     except ValueError:
#         pass

#     if symbol_info:
#         response_message = ""
#         for info, info_value in symbol_info.items():
#             response_message += "{key}:\t{value}\n".format(
#                 key=info, value=info_value)
#         bot.reply_to(message, response_message)
#         states[user_id] = _START_STATE
#     else:
#         bot.reply_to(message, _I18N['unknown_symbol'][lang])

add_transaction_regex = re.compile("[0-9]{0-10}")


class FinanceBot:
    def __init__(self, telegram_api_token: Text, alpha_vantage_api_token: Text,
                 redis_address: Text = "localhost", path_to_db: Text = "db/"):
        self.bot = telebot.TeleBot(telegram_api_token)
        self.stock_api = alpha_vantage.TimeSeries(alpha_vantage_api_token)
        self.state = StateKeeper(host=redis_address, decode_responses=True)
        self.storage = storage.Storage(path_to_db)

    def polling(self):

        def dispatcher(messages):
            for message in messages:
                message_text = message.text.lower()
                # The very first interaction with the bot.
                if message_text == "/start":
                    self.greeting(message)

        self.bot.set_update_listener(dispatcher)
        self.bot.polling()

    def greeting(self, message):
        lang = message.from_user.language_code or 'en'
        chat_id = message.chat.id

        self.state[chat_id] = State.START_STATE
        self.bot.send_message(chat_id, _I18N['greeting_message'][lang])


def main():
    if not _ALPHAVANTAGE_API_KEY:
        sys.exit(
            "Alpha Vantage API token not found in ENV variables. Please set ALPHAVANTAGE_API_KEY env variable.")
    if not _TELEGRAM_BOT_TOKEN:
        sys.exit(
            "Telegram Bot token not found in ENV variables. Please set TELEGRAM_BOT_TOKEN env variable.")
    bot = FinanceBot(_TELEGRAM_BOT_TOKEN, _ALPHAVANTAGE_API_KEY)
    bot.polling()


if __name__ == "__main__":
    main()
