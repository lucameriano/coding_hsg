import numpy as np
from sortedcontainers import SortedDict
import matplotlib.pyplot as plt

from start import match_order, cancel_limit_order


def generate_price(type, bids, asks, ref):
    if type == "buy":
        anchor = bids.peekitem(-1)[0] if bids else ref  # best bid
    elif type == "sell":
        anchor = asks.peekitem(0)[0] if asks else ref  # best ask
    else:
        raise TypeError(f"Wrong type: {type}")

    # Random price
    return anchor + int(np.random.randint(-2, 3))


bids = SortedDict({99: 10, 99.5: 10, 100: 10})
asks = SortedDict({102: 10, 101.5: 10, 101: 10})

np.random.seed(100)

decisions = 2000
trades_combined = []

choices = [
    "nothing",
    "buy_limit",
    "sell_limit",
    "buy_market",
    "sell_market",
    "cancel_buy_limit",
    "cancel_sell_limit",
]
probabilities = [0.10, 0.25, 0.25, 0.08, 0.08, 0.12, 0.12]
ref = 100

for _ in range(decisions):
    choice = np.random.choice(choices, p=probabilities)
    quantity = np.random.choice(range(1, 10))

    if choice == "nothing":
        trades = []

    elif choice == "buy_limit":
        price = generate_price("buy", bids, asks, ref)
        trades, remaining = match_order("buy", price, quantity, bids, asks)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            # get(..., 0) avoids a KeyError
            bids[price] = bids.get(price, 0) + remaining

    elif choice == "sell_limit":
        price = generate_price("sell", bids, asks, ref)
        trades, remaining = match_order("sell", price, quantity, bids, asks)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            asks[price] = asks.get(price, 0) + remaining

    elif choice == "buy_market":
        market_order = True
        trades, unfilled = match_order(
            "buy", 0, quantity, bids, asks, market_order=market_order
        )

    elif choice == "sell_market":
        market_order = True
        trades, unfilled = match_order(
            "sell", 0, quantity, bids, asks, market_order=market_order
        )

    elif choice == "cancel_buy_limit":
        price = generate_price("buy", bids, asks, ref)
        cancel_limit_order("buy", price, quantity, bids, asks)
        trades = []

    elif choice == "cancel_sell_limit":
        price = generate_price("sell", bids, asks, ref)
        cancel_limit_order("sell", price, quantity, bids, asks)
        trades = []

    trades_combined.append(trades)

prices = [p for trades in trades_combined for (p, q) in trades]
plt.plot(prices)
plt.show()
