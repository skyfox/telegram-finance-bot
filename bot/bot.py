"""Telegram bot for expenses tracking."""

import collections
import datetime
import json
import logging
import os
import random
import re
import sys
from typing import Text

import telegram as telegram_internal
import telegram.ext as telegram

import ledger_pb2
import storage

_i18n_data = open("i18n.json", "r")
_I18N = json.loads(_i18n_data.read())
_i18n_data.close()


class FilterExpense(telegram.BaseFilter):
    """The filter for expense records.

    Implements filter method only.
    """

    def filter(self, update: telegram_internal.Update) -> bool:
        """Matches update's text with the regex."""
        # Matches "10 grocery", "12.82 shopping"
        # Does not match "12.82 shopping and car"
        pattern = r"^[0-9]+\.{0,1}[0-9]* [a-zA-Z]*$"
        if re.match(pattern, update.text):
            return True
        return False


filter_expense = FilterExpense()


def handler_start(update: telegram_internal.Update,
                  context: telegram.callbackcontext.CallbackContext) -> None:
    """Handles /start commands and welcomes users."""
    chat_id = update.effective_chat.id
    lang = update.effective_user.language_code or "en"
    context.bot.send_message(
        chat_id=chat_id, text=_I18N["greeting_message"][lang])


def handler_not_understand(update: telegram_internal.Update,
                           context: telegram.callbackcontext.CallbackContext) -> None:
    """Handle all other messages."""
    chat_id = update.effective_chat.id
    lang = update.effective_user.language_code or "en"
    context.bot.send_message(
        chat_id=chat_id, text=_I18N["do_not_understand"][lang])


class FinanceBot:
    """The main class of the bot."""

    def __init__(self, telegram_api_token: Text, path_to_db: Text = "db/") -> None:
        self.bot = telegram.Updater(token=telegram_api_token, use_context=True)
        self.storage = storage.Storage(path_to_db)

    def dispatch(self) -> None:
        """Dispatches all active handlers."""
        dispatcher = self.bot.dispatcher

        start_handler = telegram.CommandHandler("start", handler_start)
        dispatcher.add_handler(start_handler)
        expense_handler = telegram.MessageHandler(
            filter_expense, self.handler_expense)
        dispatcher.add_handler(expense_handler)
        report_handler = telegram.CommandHandler("report", self.handler_report)
        dispatcher.add_handler(report_handler)
        unknown_handler = telegram.MessageHandler(
            telegram.Filters.all, handler_not_understand)
        dispatcher.add_handler(unknown_handler)

    def handler_report(self, update: telegram_internal.Update,
                       context: telegram.callbackcontext.CallbackContext) -> None:
        """Handles /report command and generates report for a current month."""
        chat_id = update.effective_chat.id
        today = datetime.date.today()
        transactions = self.storage.find_transactions(
            chat_id=chat_id, year=today.year, month=today.month)
        report = collections.defaultdict(float)
        for transaction in transactions:
            report[transaction.category] += transaction.amount
        text_report = "\n".join(";".join((k, str(v)))
                                for k, v in report.items())
        context.bot.send_message(chat_id=chat_id, text=text_report)

    def handler_expense(self, update: telegram_internal.Update,
                        context: telegram.callbackcontext.CallbackContext) -> None:
        """Handles expense message."""
        chat_id = update.effective_chat.id
        message_id = update.message.message_id if update.message else update.edited_message.message_id
        message_datetime = update.message.date if update.message else update.edited_message.date
        lang = update.effective_user.language_code or "en"

        amount, category = (update.message.text.split() if update.message
                            else update.edited_message.text.split())
        transaction = ledger_pb2.ExpenseTransaction(
            category=category, amount=float(amount))

        if update.message:
            self.storage.write_transaction(
                chat_id, message_id, message_datetime, transaction)
            context.bot.send_message(
                chat_id=chat_id, text=random.choice(_I18N["transaction_completed"][lang]))
        elif update.edited_message:
            self.storage.update_transaction(
                chat_id, message_id, message_datetime, transaction)
            context.bot.send_message(
                chat_id=chat_id, text=random.choice(_I18N["transaction_edited"][lang]))

    def start_polling(self) -> None:
        """Preps the bot and starts polling."""
        self.dispatch()
        self.bot.start_polling()
        self.bot.idle()


def main():
    telegram_bot_api_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_api_token:
        sys.exit(
            "Telegram Bot token not found in ENV variables. Please set TELEGRAM_BOT_TOKEN env variable.")

    logging_level = logging.WARNING
    if os.environ.get("env") == "dev":
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level)

    storage_path = os.environ.get("PATH_TO_STORAGE", "db/")

    bot = FinanceBot(telegram_bot_api_token, storage_path)
    bot.start_polling()


if __name__ == "__main__":
    main()
