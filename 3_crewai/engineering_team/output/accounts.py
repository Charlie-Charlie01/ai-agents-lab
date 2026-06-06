class Account:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.balance = 0.0
        self.holdings = {}
        self.transactions = []
        self.initial_deposit = 0.0

    def create_account(self) -> None:
        self.balance = 0.0
        self.holdings = {}
        self.transactions = []

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        if self.initial_deposit == 0:
            self.initial_deposit = amount
        self.transactions.append({
            'action': 'deposit',
            'amount': amount,
            'timestamp': self._current_time()
        })

    def withdraw(self, amount: float) -> None:
        if amount > self.balance:
            raise ValueError("Cannot withdraw more than current balance.")
        self.balance -= amount
        self.transactions.append({
            'action': 'withdraw',
            'amount': amount,
            'timestamp': self._current_time()
        })

    def buy_shares(self, symbol: str, quantity: int) -> None:
        share_price = get_share_price(symbol)
        total_cost = share_price * quantity
        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append({
            'action': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price': share_price,
            'timestamp': self._current_time()
        })

    def sell_shares(self, symbol: str, quantity: int) -> None:
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError("Not enough shares to sell.")
        share_price = get_share_price(symbol)
        total_income = share_price * quantity
        self.balance += total_income
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        self.transactions.append({
            'action': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price': share_price,
            'timestamp': self._current_time()
        })

    def get_portfolio_value(self) -> float:
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def get_profit_or_loss(self) -> float:
        current_value = self.get_portfolio_value()
        return current_value - self.initial_deposit

    def get_holdings(self) -> dict:
        return self.holdings

    def get_transactions(self) -> list:
        return self.transactions

    def _current_time(self):
        from datetime import datetime
        return datetime.now().isoformat()

def get_share_price(symbol: str) -> float:
    prices = {
        'AAPL': 150.00,
        'TSLA': 900.00,
        'GOOGL': 2800.00
    }
    return prices.get(symbol, 0.0)