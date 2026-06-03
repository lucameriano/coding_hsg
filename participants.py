import numpy as np
from sortedcontainers import SortedDict

from start import match_order, cancel_limit_order

bids = SortedDict({99: 10, 99.5: 10, 100: 10})
asks = SortedDict({102: 10, 101.5: 10, 101: 10})

decisions = 100
trades_combined = []

for i in range(decisions):
    # CHOICES:
    # do nothing
    # buy limit order
    # sell limit order
    # buy market order
    # sell market order
    # cancel buy limit order
    # cancel sell limit order

    choice = np.random.choice(range(0, 7))

    if choice == 0:
        trades = []

    elif choice == 1:
        price = 101
        quantity = np.random.choice(range(1, 100))
        trades, remaining = match_order("buy", price, quantity, bids, asks)
        print(trades)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            # get(..., 0) avoids a KeyError
            bids[price] = bids.get(price, 0) + remaining

    elif choice == 2:
        price = 101
        quantity = np.random.choice(range(1, 100))
        trades, remaining = match_order("sell", price, quantity, bids, asks)
        print(trades)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            asks[price] = asks.get(price, 0) + remaining

    elif choice == 3:
        quantity = np.random.choice(range(1, 100))
        market_order = True
        trades, unfilled = match_order(
            "buy", 0, quantity, bids, asks, market_order=market_order
        )

    elif choice == 4:
        quantity = np.random.choice(range(1, 100))
        market_order = True
        trades, unfilled = match_order(
            "sell", 0, quantity, bids, asks, market_order=market_order
        )

    elif choice == 5:
        price = 101
        quantity = np.random.choice(range(1, 100))
        cancel_limit_order("buy", price, quantity, bids, asks)
        trades = []

    elif choice == 6:
        price = 101
        quantity = np.random.choice(range(1, 100))
        cancel_limit_order("sell", price, quantity, bids, asks)
        trades = []

    trades_combined.append(trades)
