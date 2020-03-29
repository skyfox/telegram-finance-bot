import sys
import os
import unittest
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot import storage, ledger_pb2

_DB_TEST_FOLDER = "/tmp/telegram-finance-bot-test-storage/"


class StorageTest(unittest.TestCase):
    """Advanced test cases."""

    def setUp(self) -> None:
        self.storage = storage.Storage(_DB_TEST_FOLDER)

    def tearDown(self) -> None:
        self.storage._db.close()
        shutil.rmtree(_DB_TEST_FOLDER)

    def test_write_transaction(self) -> None:
        transaction = ledger_pb2.ExpenseTransaction(category="category", amount=42)
        self.storage.write_transaction(1234, transaction)
        result = ledger_pb2.ExpenseTransaction().FromString(
            [t for t in self.storage._db.iterator(prefix=b"1234")][0][1])
        self.assertEqual(transaction, result)

    def test_find_transactions(self) -> None:
        transaction_1 = ledger_pb2.ExpenseTransaction(category="category1", amount=100)
        transaction_2 = ledger_pb2.ExpenseTransaction(category="category1", amount=300)
        transaction_3 = ledger_pb2.ExpenseTransaction(category="category2", amount=300)

        self.storage._db.put(b"1234-2020-10-29-20-00-00", transaction_1.SerializeToString())
        self.storage._db.put(b"1234-2020-10-30-20-00-00", transaction_2.SerializeToString())
        self.storage._db.put(b"1234-2020-11-30-20-00-00", transaction_3.SerializeToString())

        yearly_transactions = [t for t in self.storage.find_transactions(1234, year=2020)]
        self.assertEqual(3, len(yearly_transactions))
        monthly_transactions = [t for t in self.storage.find_transactions(1234, year=2020, month=10)]
        self.assertEqual(2, len(monthly_transactions))
        daily_transactions = [t for t in self.storage.find_transactions(1234, year=2020, month=11, day=30)]
        self.assertEqual(1, len(daily_transactions))
        no_transactions = [t for t in self.storage.find_transactions(1234, year=2020, month=3, day=30)]
        self.assertEqual(0, len(no_transactions))


if __name__ == '__main__':
    unittest.main()
