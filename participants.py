import numpy as np
from sortedcontainers import SortedDict

from start import match_order, cancel_limit_order


def place_price(type, bids, asks, ref):
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

decisions = 100
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

for _ in range(decisions):
    # CHOICES: 0-7
    # do nothing
    # buy limit order
    # sell limit order
    # buy market order
    # sell market order
    # cancel buy limit order
    # cancel sell limit order

    choice = np.random.choice(range(0, 7))

    # do nothing
    if choice == 0:
        trades = []

    # buy limit order
    elif choice == 1:
        price = 101
        quantity = np.random.choice(range(1, 100))
        trades, remaining = match_order("buy", price, quantity, bids, asks)
        print(trades)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            # get(..., 0) avoids a KeyError
            bids[price] = bids.get(price, 0) + remaining

    # sell limit order
    elif choice == 2:
        price = 101
        quantity = np.random.choice(range(1, 100))
        trades, remaining = match_order("sell", price, quantity, bids, asks)
        print(trades)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            asks[price] = asks.get(price, 0) + remaining

    # buy market order
    elif choice == 3:
        quantity = np.random.choice(range(1, 100))
        market_order = True
        trades, unfilled = match_order(
            "buy", 0, quantity, bids, asks, market_order=market_order
        )

    # sell market order
    elif choice == 4:
        quantity = np.random.choice(range(1, 100))
        market_order = True
        trades, unfilled = match_order(
            "sell", 0, quantity, bids, asks, market_order=market_order
        )

    # cancel buy limit order
    elif choice == 5:
        price = 101
        quantity = np.random.choice(range(1, 100))
        cancel_limit_order("buy", price, quantity, bids, asks)
        trades = []

    # cancel sell limit order
    elif choice == 6:
        price = 101
        quantity = np.random.choice(range(1, 100))
        cancel_limit_order("sell", price, quantity, bids, asks)
        trades = []

    trades_combined.append(trades)
