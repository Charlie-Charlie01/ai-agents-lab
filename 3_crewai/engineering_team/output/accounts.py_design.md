```markdown
# Module: accounts.py

## Overview
This module provides a simple account management system for a trading simulation platform, allowing users to create accounts, manage funds, and execute buy and sell transactions. It calculates portfolio values, reports holdings, and tracks transactions over time. The system ensures users cannot perform illegal operations such as overdrawing their account or selling shares they do not own.

## Class: Account

### Attributes:
- `user_id` (str): Unique identifier for the user.
- `balance` (float): The current balance of the user's account.
- `holdings` (dict): A dictionary mapping stock symbols to quantities owned by the user.
- `transactions` (list): A list of transaction records, each represented as a dictionary.

### Methods:

#### `__init__(self, user_id: str) -> None`
Constructor that initializes the account with a user ID and a starting balance of 0.

- **Parameters:**
  - `user_id`: Unique identifier for the user's account.

#### `create_account(self) -> None`
Initializes a new account for the user.

#### `deposit(self, amount: float) -> None`
Adds the specified amount to the user's account balance.

- **Parameters:**
  - `amount`: The amount to deposit into the account.

- **Raises:**
  - `ValueError`: If the amount is non-positive.

#### `withdraw(self, amount: float) -> None`
Reduces the user's account balance by the specified amount.

- **Parameters:**
  - `amount`: The amount to withdraw from the account.

- **Raises:**
  - `ValueError`: If the withdrawal amount exceeds the current balance, which would result in a negative balance.

#### `buy_shares(self, symbol: str, quantity: int) -> None`
Records that the user has bought a specified quantity of shares of a given stock.

- **Parameters:**
  - `symbol`: The stock symbol to buy.
  - `quantity`: The number of shares to buy.

- **Raises:**
  - `ValueError`: If the user cannot afford to buy the shares.

#### `sell_shares(self, symbol: str, quantity: int) -> None`
Records that the user has sold a specified quantity of shares of a given stock.

- **Parameters:**
  - `symbol`: The stock symbol to sell.
  - `quantity`: The number of shares to sell.

- **Raises:**
  - `ValueError`: If the user does not have enough shares to sell.

#### `get_portfolio_value(self) -> float`
Calculates and returns the total value of the user's portfolio based on current share prices.

- **Returns:**
  - Total portfolio value as a float.

#### `get_profit_or_loss(self) -> float`
Calculates and returns the profit or loss the user has made since the initial deposit.

- **Returns:**
  - Profit or loss as a float.

#### `get_holdings(self) -> dict`
Returns a dictionary with the user's current stock holdings (symbol and quantity).

- **Returns:**
  - Dictionary of stock holdings.

#### `get_transactions(self) -> list`
Returns a list of all transactions made by the user.

- **Returns:**
  - List of transactions.

## Function: get_share_price

### Signature:
```python
def get_share_price(symbol: str) -> float
```

### Description:
Returns the current price of a share for the given stock symbol. This function provides mocked prices for the purpose of simulation.

- **Parameters:**
  - `symbol`: The stock symbol for which the price is requested.

- **Returns:**
  - The current share price as a float.

### Mock Implementation:
- For testing purposes, this function will return fixed prices:
  - AAPL: 150.00
  - TSLA: 900.00
  - GOOGL: 2800.00

## Example of Transaction Structure
A transaction will be represented as a dictionary and may contain:
- `action`: ('buy' or 'sell')
- `symbol`: the stock symbol
- `quantity`: the number of shares involved
- `price`: the price per share at the time of transaction
- `timestamp`: the date and time of the transaction

```
This design provides a comprehensive and clear overview of the classes and methods to implement the requested account management system. The `Account` class encapsulates all necessary functionalities while maintaining an organized structure, leading to easier testing and UI integration.
```