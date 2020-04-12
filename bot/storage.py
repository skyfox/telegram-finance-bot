from datetime import datetime
from typing import Iterator, Optional, Text

import plyvel

import ledger_pb2


def _make_key(chat_id: int, message_id: int, message_datetime: datetime) -> Text:
    key = "-".join((str(chat_id),
                    message_datetime.strftime("%Y-%m-%d-%H-%M-%S"),
                    str(message_id)))
    return bytes(key.encode("utf-8"))


class Storage:
    """LevelDB-based data storage for bot data.

    Params:
        path: the path to the DB file.
    """

    def __init__(self, path: Text) -> None:
        self._db = plyvel.DB(path, create_if_missing=True)

    def __del__(self):
        if not self._db.closed:
            self._db.close()

    def write_transaction(self, chat_id: int, message_id: int, message_datetime: datetime, transaction: ledger_pb2.ExpenseTransaction) -> None:
        """Adds expense transaction to the DB.

        Args:
            chat_id: Telegram chat ID.
            transaction: expense transaction.
        """
        self._db.put(_make_key(chat_id, message_id, message_datetime),
                     transaction.SerializeToString())

    def update_transaction(self, chat_id: int, message_id: int, message_datetime: datetime, transaction: ledger_pb2.ExpenseTransaction) -> None:
        self._db.delete(_make_key(chat_id, message_id, message_datetime))
        self.write_transaction(chat_id, message_id,
                               message_datetime, transaction)

    def find_transactions(self, chat_id: int, year: Optional[int] = None, month: Optional[int] = None,
                          day: Optional[int] = None) -> Iterator[ledger_pb2.ExpenseTransaction]:
        """Gets all transactions for a given chat.

        Args:
            chat_id: Telegram chat ID.
            year: year of a transaction.
            month: month of a transaction.
            day: day of a transaction.

        Yields:
            a transaction.
        """
        key_params = []
        if year:
            key_params.append(str(year))
        if month:
            key_params.append('{:02d}'.format(month))
        if day:
            key_params.append('{:02d}'.format(day))
        key = "-".join((str(chat_id), *key_params))

        for _, transaction in self._db.iterator(prefix=bytes(key.encode("utf-8"))):
            yield ledger_pb2.ExpenseTransaction().FromString(transaction)
