import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sortedcontainers import SortedDict
from orders import match_order, cancel_limit_order


# Define how the price for the limit order creation gets chosen
def generate_price(type, bids, asks, ref, expectation):
    tick = 0.05
    # offset < 0 crosses the quote (keeps spread low and things trade)
    # offset > 0 rests behind the midprice
    offset = np.random.normal(loc=1 * tick, scale=1.0 * tick)

    if type == "buy":
        anchor = bids.peekitem(-1)[0] if bids else ref
        return round(anchor * (1 + expectation) - offset, 2)
    elif type == "sell":
        anchor = asks.peekitem(0)[0] if asks else ref
        return round(anchor * (1 + expectation) + offset, 2)
    else:
        raise TypeError(f"Wrong type: {type}")


# This function simulates the participant's acttions
# Decisions is the number of participant choices that get made
def simulate(decisions=50_000, seed=100):
    # Set randomness
    np.random.seed(seed)

    # Starting order book
    bids = SortedDict({99.9: 150, 99.95: 300, 100: 40})
    asks = SortedDict({100.15: 150, 100.1: 300, 100.05: 40})

    # Starting midprice
    best_bid = bids.peekitem(-1)[0]
    best_ask = asks.peekitem(0)[0]

    # Starting reference price = mid-price, which is (best bid + best ask) / 2
    # The reference price is used for the price used when creating or cancelling orders
    ref = (best_bid + best_ask) / 2

    # Define the available participant choices
    choices = [
        "nothing",
        "buy_limit",
        "sell_limit",
        "buy_market",
        "sell_market",
        "cancel_buy_limit",
        "cancel_sell_limit",
        "liquidity",
    ]

    # Pregenerate actions chosen
    probabilities = np.random.rand(decisions, len(choices))
    action_choices = np.argmax(probabilities, axis=1)

    # Randomly generated order quantities
    # A half-normal distribution (normal but cut at >= 0 is used)
    # The standard deviations of that distribution varies randomly
    std_devs_quantities = np.random.randint(1, 100, size=decisions)
    dist = np.random.normal(0, std_devs_quantities, size=decisions)
    # Set negative values to 0
    quantities = np.where(dist >= 0, dist, 0)

    # Generate an expectation for the participant, which represents the change in the fair value that the participant expects in the future
    # The standard deviations of that normal distribution with mean 0 varies randomly
    std_devs_expectations = np.abs(np.random.normal(0.00001, 0.000025, size=decisions))
    expectations = np.random.normal(0, std_devs_expectations, size=decisions)

    # Initialize vars for liquidity action later
    lp_active_bid = None
    lp_active_ask = None

    # Create the list of the final data to be used later
    timestamped_data = []

    for i in range(decisions):
        # The reference price is now the current mid-price
        # Use the best bid and asks to compute the mid-price if available
        # If bids or asks is/are empty ref will still exist from the last decision loop
        if bids and asks:
            best_bid = bids.peekitem(-1)[0]
            best_ask = asks.peekitem(0)[0]
            ref = (best_bid + best_ask) / 2

        # Choose an action
        choice = choices[action_choices[i]]

        # Get a quantity for the action
        quantity = int(quantities[i])

        # Get the expectation of the price change
        expectation = expectations[i]

        # Execute the chosen action
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
            trades, remaining = match_order("sell", price, quantity * 1.01, bids, asks)

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
            price = np.random.choice(list(bids.keys())[:10]) if bids else ref
            cancel_limit_order("buy", price, quantity, bids, asks)
            trades = []

        elif choice == "cancel_sell_limit":
            # Cancel a random ask price. If asks is empty use reference price
            price = np.random.choice(list(asks.keys())[-10:]) if asks else ref
            cancel_limit_order("sell", price, quantity, bids, asks)
            trades = []

        elif choice == "liquidity":
            # Use lower quantity for liquidity
            lp_size = quantity / 5

            # How far from the mid the LP places quotes
            lp_spread_ticks = 2
            lp_TICK = 0.01

            # Cancel old LP quotes to avoid stale orders
            if lp_active_bid is not None and lp_active_bid in bids:
                cancel_limit_order("buy", lp_active_bid, lp_size, bids, asks)
            if lp_active_ask is not None and lp_active_ask in asks:
                cancel_limit_order("sell", lp_active_ask, lp_size, bids, asks)

            # Calculate new quotes based on current reference price
            # Rounding prevents fragmented books
            new_bid_price = round(ref - (lp_spread_ticks * lp_TICK), 2)
            new_ask_price = round(ref + (lp_spread_ticks * lp_TICK), 2)

            # Place the new quotes in the order book
            bids[new_bid_price] = int(bids.get(new_bid_price, 0) + lp_size)
            asks[new_ask_price] = int(asks.get(new_ask_price, 0) + lp_size)

            # Update state variables
            lp_active_bid = new_bid_price
            lp_active_ask = new_ask_price

            trades = []

        # Timestamp the trades, each timestamp is a second
        timestamp = i // 10

        # Use the mid-price as price, reference price as backup
        price = (
            (bids.peekitem(-1)[0] + asks.peekitem(0)[0]) / 2 if bids and asks else ref
        )
        qty = sum(qty for _, qty in trades)  # volume this step (0 if no trades)
        n = len(trades)
        timestamped_data.append((timestamp, price, qty, n))

    return timestamped_data


# Transform the timestamped data to 1 minute open high low close volume etc. "OHLCV"
def prepare_data(timestamped_data, verbose=False):
    df = pd.DataFrame(timestamped_data, columns=["timestamp", "price", "qty", "n"])

    # Convert the timestamp to dt and 1-minute unit
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="m", origin="2010-01-01")
    df = df.set_index("timestamp")

    # Generate open high low close from the price column
    ohlcv = df["price"].resample("1min").ohlc()

    # Add the new columns
    # Fill nans with 0
    ohlcv["volume"] = df["qty"].resample("1min").sum().fillna(0)
    ohlcv["n_trades"] = df["n"].resample("1min").sum().fillna(0).astype(int)

    # Minutes with no trades get the 0 volume und 0 trades
    ohlcv["volume"] = ohlcv["volume"].fillna(0)

    # Minutes with no trades get open high low close = close from 1 minute ago
    filler = ohlcv["close"].shift(1)
    for col in ["open", "high", "low", "close"]:
        ohlcv[col] = ohlcv[col].fillna(filler).bfill()

    if verbose:
        print(ohlcv)
        print(ohlcv["close"].isna().sum())

    return ohlcv


if __name__ == "__main__":
    timestamped_data = simulate(decisions=50_000, seed=2)
    ohlcv = prepare_data(timestamped_data, verbose=True)
    plt.plot(ohlcv["close"])
    plt.show()
