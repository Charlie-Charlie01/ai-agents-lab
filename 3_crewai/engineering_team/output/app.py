from accounts import Account
import gradio as gr

account = Account(user_id="user1")

def create_account():
    account.create_account()
    return "Account created."

def deposit(amount):
    try:
        account.deposit(amount)
        return f"Deposited: ${amount}. Current balance: ${account.balance}."
    except ValueError as e:
        return str(e)

def withdraw(amount):
    try:
        account.withdraw(amount)
        return f"Withdrew: ${amount}. Current balance: ${account.balance}."
    except ValueError as e:
        return str(e)

def buy_shares(symbol, quantity):
    try:
        account.buy_shares(symbol, quantity)
        return f"Bought {quantity} shares of {symbol}. Current holdings: {account.get_holdings()}"
    except ValueError as e:
        return str(e)

def sell_shares(symbol, quantity):
    try:
        account.sell_shares(symbol, quantity)
        return f"Sold {quantity} shares of {symbol}. Current holdings: {account.get_holdings()}"
    except ValueError as e:
        return str(e)

def portfolio_value():
    value = account.get_portfolio_value()
    return f"Total portfolio value: ${value}"

def profit_or_loss():
    profit_loss = account.get_profit_or_loss()
    return f"Profit/Loss: ${profit_loss}"

def transaction_history():
    transactions = account.get_transactions()
    return transactions

interface = gr.Interface(
    fn=create_account,
    inputs=[],
    outputs="text",
    title="Account Management",
    description="Manage your trading simulation account."
)

deposit_interface = gr.Interface(
    fn=deposit,
    inputs="number",
    outputs="text",
    title="Deposit Funds"
)

withdraw_interface = gr.Interface(
    fn=withdraw,
    inputs="number",
    outputs="text",
    title="Withdraw Funds"
)

buy_interface = gr.Interface(
    fn=buy_shares,
    inputs=["text", "number"],
    outputs="text",
    title="Buy Shares"
)

sell_interface = gr.Interface(
    fn=sell_shares,
    inputs=["text", "number"],
    outputs="text",
    title="Sell Shares"
)

portfolio_value_interface = gr.Interface(
    fn=portfolio_value,
    inputs=[],
    outputs="text",
    title="Portfolio Value"
)

profit_loss_interface = gr.Interface(
    fn=profit_or_loss,
    inputs=[],
    outputs="text",
    title="Profit or Loss"
)

transaction_history_interface = gr.Interface(
    fn=transaction_history,
    inputs=[],
    outputs="json",
    title="Transaction History"
)

demo = gr.TabbedInterface([interface, deposit_interface, withdraw_interface, buy_interface, sell_interface, portfolio_value_interface, profit_loss_interface, transaction_history_interface], ["Create Account", "Deposit", "Withdraw", "Buy Shares", "Sell Shares", "Portfolio Value", "Profit or Loss", "Transaction History"])

demo.launch()