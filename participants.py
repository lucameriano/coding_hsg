import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sortedcontainers import SortedDict
from orders import match_order, cancel_limit_order


# Define how the price for the limit order creation gets chosen
def generate_price(
    side: str, bids: SortedDict, asks: SortedDict, ref: float, expectation: float
) -> float:
    # Validation
    if not isinstance(side, str):
        raise TypeError(f"side must be an str, got {type(side)}")
    if not isinstance(bids, SortedDict):
        raise TypeError(f"Wrong type for bids: {type(bids)}")
    if not isinstance(asks, SortedDict):
        raise TypeError(f"Wrong type for asks: {type(asks)}")
    if not isinstance(ref, (float, np.floating)):
        raise TypeError(f"Wrong type for ref: {type(ref)}")
    if not isinstance(expectation, (float, np.floating)):
        raise TypeError(f"Wrong type for expectation: {type(expectation)}")

    # offset is drawn from a normal distribution centered slightly above 0 (mean = +1 tick)
    # This means most orders rest passively behind the midprice, which is realistic.
    # When offset happens to be negative, the order crosses the spread and trades immediately.
    tick = 0.05
    offset = np.random.normal(loc=1 * tick, scale=1 * tick)

    # anchor is the best price on the same side: best bid for buys, best ask for sells.
    # Falls back to the reference (mid) price if that side of the book is empty.
    # Expectation shifts the anchor before the random offset is applied.
    if side == "buy":
        anchor = bids.peekitem(-1)[0] if bids else ref
        return round(anchor * (1 + expectation) - offset, 2)
    elif side == "sell":
        anchor = asks.peekitem(0)[0] if asks else ref
        return round(anchor * (1 + expectation) + offset, 2)
    else:
        raise TypeError(f"Wrong side: {side}. Has to be 'buy' or 'sell'.")


# This function simulates the participant's actions
# Decisions is the number of participant choices that get made
def simulate(decisions: int = 50_000, seed: int = 100) -> list[tuple]:
    # Validation
    if not isinstance(decisions, int):
        raise TypeError(f"decisions must be an int, got {type(decisions)}")
    if not isinstance(seed, int):
        raise TypeError(f"seed must be an int, got {type(seed)}")
    if decisions <= 0:
        raise ValueError("Increase the number of decisions for the simulation")

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
    # The highest generated probability defines the action
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
    std_devs_expectations_mean = 0.00001
    std_devs_expectations_std_dev = 0.000025
    std_devs_expectations = np.abs(
        np.random.normal(
            std_devs_expectations_mean, std_devs_expectations_std_dev, size=decisions
        )
    )
    expectations = np.random.normal(0, std_devs_expectations, size=decisions)

    # Initialize vars for liquidity action later
    lp_active_bid = None
    lp_active_ask = None

    # Initialize for safety
    best_bid_price = best_ask_price = ref

    # How far from the mid the liquidity action places quotes
    lp_spread_ticks = 2
    # lp_TICK is the minimum price increment (0.01).
    # quotes are placed lp_spread_ticks ticks from mid on each side
    lp_TICK = 0.01

    # The liquidity quantity will get divided by this denominator
    liquidity_quantity_denominator = 5

    # How many levels of the orderbook are considered for possible limit order cancellation
    top_levels_cancellation = 10

    # Create the list of the final data to be used later
    timestamped_data = []

    # Loop through the decisions
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
            price = (
                np.random.choice(list(bids.keys())[:top_levels_cancellation])
                if bids
                else ref
            )
            cancel_limit_order("buy", price, quantity, bids, asks)
            trades = []

        elif choice == "cancel_sell_limit":
            # Cancel a random ask price. If asks is empty use reference price
            price = (
                np.random.choice(list(asks.keys())[-top_levels_cancellation:])
                if asks
                else ref
            )
            cancel_limit_order("sell", price, quantity, bids, asks)
            trades = []

        elif choice == "liquidity":
            # Use lower quantity for liquidity
            lp_size = quantity / liquidity_quantity_denominator

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

        # Each minute contains 10 decisions, so integer-divide the decision index to get the minute timestamp.
        timestamp = i // 10

        # Pull the best bid and best ask incl. quantities
        if bids:
            best_bid_price, best_bid_qty = bids.peekitem(-1)
        else:
            best_bid_qty = 0
        if asks:
            best_ask_price, best_ask_qty = asks.peekitem(0)
        else:
            best_ask_qty = 0

        # Use the mid-price as price, reference price as backup
        price = (best_bid_price + best_ask_price) / 2 if bids and asks else ref

        # total volume traded this step (0 if no trades)
        qty = sum(qty for _, qty in trades)

        # Trade count
        n = len(trades)

        timestamped_data.append((timestamp, price, qty, n, best_bid_qty, best_ask_qty))

    return timestamped_data


# Transform the timestamped data to 1 minute open high low close volume etc. "OHLCV"
def prepare_data(timestamped_data: list[tuple], verbose: bool = False) -> pd.DataFrame:
    # Validation
    if not isinstance(timestamped_data, list):
        raise TypeError(
            f"timestamped_data must be a list, got {type(timestamped_data)}"
        )
    if not isinstance(verbose, bool):
        raise TypeError(f"verbose must be bool, got {type(verbose)}")
    if not timestamped_data:
        raise ValueError("timestamped_data is empty")

    df = pd.DataFrame(
        timestamped_data,
        columns=["timestamp", "price", "qty", "n", "best_bid_qty", "best_ask_qty"],
    )

    # Convert the timestamp to dt and 1-minute unit
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="m", origin="2010-01-01")
    df = df.set_index("timestamp")

    # Generate open high low close from the price column
    ohlcv = df["price"].resample("1min").ohlc()

    # Add the new columns
    # Fill nans with 0
    # Minutes with no trades get the 0 volume und 0 trades
    ohlcv["volume"] = df["qty"].resample("1min").sum().fillna(0)
    ohlcv["n_trades"] = df["n"].resample("1min").sum().fillna(0).astype(int)

    # Use the most recent bid and ask quantities
    ohlcv["best_bid_qty"] = df["best_bid_qty"].resample("1min").last().fillna(0)
    ohlcv["best_ask_qty"] = df["best_ask_qty"].resample("1min").last().fillna(0)

    # Minutes with no trades get open high low close = close from 1 minute ago
    filler = ohlcv["close"].shift(1)
    for col in ["open", "high", "low", "close"]:
        ohlcv[col] = ohlcv[col].fillna(filler).bfill()
        # Note: bfill handles the edge case where the first minute has no prior close to fill from

    if verbose:
        print(ohlcv)
        print(ohlcv["close"].isna().sum())

    return ohlcv


if __name__ == "__main__":
    timestamped_data = simulate(decisions=50_000, seed=1)
    ohlcv = prepare_data(timestamped_data, verbose=True)
    plt.plot(ohlcv["close"])
    plt.show()
