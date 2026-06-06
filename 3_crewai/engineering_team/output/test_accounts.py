import unittest
from accounts import Account, get_share_price

class TestAccount(unittest.TestCase):

    def setUp(self):
        self.account = Account('user123')
        self.account.create_account()

    def test_initialization(self):
        self.assertEqual(self.account.user_id, 'user123')
        self.assertEqual(self.account.balance, 0.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(self.account.transactions, [])
        self.assertEqual(self.account.initial_deposit, 0.0)

    def test_deposit(self):
        self.account.deposit(100.0)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(len(self.account.transactions), 1)
        self.assertEqual(self.account.transactions[0]['action'], 'deposit')

    def test_deposit_negative(self):
        with self.assertRaises(ValueError):
            self.account.deposit(-50)

    def test_withdraw(self):
        self.account.deposit(100.0)
        self.account.withdraw(50.0)
        self.assertEqual(self.account.balance, 50.0)

    def test_withdraw_exceed_balance(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(50.0)

    def test_buy_shares(self):
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 2)
        self.assertEqual(self.account.holdings['AAPL'], 2)
        self.assertEqual(self.account.balance, 700.0)

    def test_buy_shares_insufficient_funds(self):
        self.account.deposit(100.0)
        with self.assertRaises(ValueError):
            self.account.buy_shares('TSLA', 2)

    def test_sell_shares(self):
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 2)
        self.account.sell_shares('AAPL', 1)
        self.assertEqual(self.account.holdings['AAPL'], 1)
        self.assertEqual(self.account.balance, 850.0)

    def test_sell_shares_insufficient_holdings(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares('AAPL', 1)

    def test_get_portfolio_value(self):
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 2)
        self.assertAlmostEqual(self.account.get_portfolio_value(), 1000.0 + 2 * get_share_price('AAPL'))

    def test_get_profit_or_loss(self):
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 2)
        self.assertAlmostEqual(self.account.get_profit_or_loss(), (1000.0 + 2 * get_share_price('AAPL')) - 1000.0)

    def test_get_holdings(self):
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 2)
        self.assertEqual(self.account.get_holdings(), {'AAPL': 2})

    def test_get_transactions(self):
        self.account.deposit(100.0)
        self.assertEqual(len(self.account.get_transactions()), 1)

if __name__ == '__main__':
    unittest.main()