import numpy as np
from sortedcontainers import SortedDict
import matplotlib.pyplot as plt

from start import match_order, cancel_limit_order


def generate_price(type, bids, asks, ref, expectation):
    if type == "buy":
        anchor = bids.peekitem(-1)[0] if bids else ref  # best bid
    elif type == "sell":
        anchor = asks.peekitem(0)[0] if asks else ref  # best ask
    else:
        raise TypeError(f"Wrong type: {type}")

    # Random price round it to 2 digits to keep orderbook not too fragmented
    random_price = round(anchor * (1 + expectation), 2)

    return random_price


# Starting order book
bids = SortedDict({99: 30, 99.5: 30, 100: 30})
asks = SortedDict({102: 30, 101.5: 30, 101: 30})
np.random.seed(100)

# Starting midprice
best_bid = bids.peekitem(-1)[0]
best_ask = asks.peekitem(0)[0]

# Starting reference price = mid-price, which is (best bid + best ask) / 2
# The reference price is used for the price used when creating or cancelling orders
ref = (best_bid + best_ask) / 2
decisions = 150_000

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

# Pregenerate randomness
action_choices = np.random.choice(len(choices), size=decisions, p=probabilities)
quantities = np.random.uniform(1, 10, size=decisions)
# Generate an expectation for the participant
# This expectation represents the change in the fair value that the participant expects in the future
expectations = np.random.uniform(-0.0005, 0.0005, size=decisions)

refs = [ref]
trades_combined = []
for i in range(decisions):
    # Reference price is now the current mid-price
    # Use the best bid and asks to compute the mid-price if available
    # else use the last ref price. refs[i-1] will always be available since current ref gets appended to refs.
    if bids and asks:
        best_bid = bids.peekitem(-1)[0]
        best_ask = asks.peekitem(0)[0]
        ref = (best_bid + best_ask) / 2
    else:
        ref = refs[i - 1]
    refs.append(ref)

    # Choose an action
    choice = choices[action_choices[i]]

    # Generate a quantity for the action
    quantity = quantities[i]

    expectation = expectations[i]

    if choice == "nothing":
        trades = []

    elif choice == "buy_limit":
        price = generate_price("buy", bids, asks, ref, expectation)
        trades, remaining = match_order("buy", price, quantity, bids, asks)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            # get(..., 0) avoids a KeyError
            bids[price] = bids.get(price, 0) + remaining

    elif choice == "sell_limit":
        price = generate_price("sell", bids, asks, ref, expectation)
        trades, remaining = match_order("sell", price, quantity, bids, asks)

        # Rest the remaining part of the order, add it to the relevant book
        if remaining > 0:
            asks[price] = asks.get(price, 0) + remaining

    elif choice == "buy_market":
        market_order = True
        # Use price 0 as the limit_price since the limit_price is irrelevant for market orders
        trades, unfilled = match_order(
            "buy", 0, quantity, bids, asks, market_order=market_order
        )

    elif choice == "sell_market":
        market_order = True
        # Use price 0 as the limit_price since the limit_price is irrelevant for market orders
        trades, unfilled = match_order(
            "sell", 0, quantity, bids, asks, market_order=market_order
        )

    elif choice == "cancel_buy_limit":
        # Cancel a random bid price. If bids is empty use reference price
        price = np.random.choice(list(bids.keys())) if bids else ref
        cancel_limit_order("buy", price, quantity, bids, asks)
        trades = []

    elif choice == "cancel_sell_limit":
        # Cancel a random ask price. If asks is empty use reference price
        price = np.random.choice(list(asks.keys())) if asks else ref
        cancel_limit_order("sell", price, quantity, bids, asks)
        trades = []

    trades_combined.append(trades)


prices = [p for trades in trades_combined for (p, q) in trades]
plt.plot(prices)
plt.show()
