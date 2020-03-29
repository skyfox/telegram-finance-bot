import os
import sys

import alpha_vantage.timeseries as alpha_vantage
import telebot
import redis

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

# States
_START_STATE = "start"
_CLARIFY_SYMBOL = 'clarify symbol'


class StateKeeper(redis.Redis):
    def __getitem__(self, user_id):
        state = self.get(user_id)
        if not state:
            self.set(user_id, _START_STATE)
            return _START_STATE
        return state

    def __setitem__(self, user_id, state):
        return self.set(user_id, state)


states = StateKeeper(decode_responses=True)
stock_api = alpha_vantage.TimeSeries(_ALPHAVANTAGE_API_KEY)
bot = telebot.TeleBot(_TELEGRAM_BOT_TOKEN)


@bot.message_handler(func=lambda message: states[message.from_user.id] == _START_STATE)
def main_handler(message):
    lang = message.from_user.language_code or 'en'
    user_id = message.from_user.id
    message_text = message.text.lower()

    if message_text == "/start":
        bot.send_message(message.chat.id, _I18N['greeting_message'][lang])
    elif "stock price" in message_text:
        states[user_id] = _CLARIFY_SYMBOL
        bot.send_message(message.chat.id, _I18N['clarify_symbol'][lang])
    else:
        bot.send_message(message.chat.id, _I18N['do_not_understand'][lang])


@bot.message_handler(func=lambda message: states[message.from_user.id] == _CLARIFY_SYMBOL)
def get_quote_handler(message):
    lang = message.from_user.language_code or 'en'
    user_id = message.from_user.id
    message_text = message.text.lower()

    symbol_info = None
    try:
        bot.send_chat_action(message.chat.id, "typing")
        symbol_info, _ = stock_api.get_quote_endpoint(message_text)
    except ValueError:
        pass

    if symbol_info:
        response_message = ""
        for info, info_value in symbol_info.items():
            response_message += "{key}:\t{value}\n".format(key=info, value=info_value)
        bot.reply_to(message, response_message)
        states[user_id] = _START_STATE
    else:
        bot.reply_to(message, _I18N['unknown_symbol'][lang])


def main():
    if not _ALPHAVANTAGE_API_KEY:
        sys.exit("Alpha Vantage API token not found in ENV variables. Please set ALPHAVANTAGE_API_KEY env variable.")
    if not _TELEGRAM_BOT_TOKEN:
        sys.exit("Telegram Bot token not found in ENV variables. Please set TELEGRAM_BOT_TOKEN env variable.")
    bot.polling()


if __name__ == "__main__":
    main()
