from sortedcontainers import SortedDict

"""
match_order generates trades i. e. tries to match an order with the existing book.
It returns the trades done and the leftover quantity (relevant for big orders that cannot be fully filled).

It handles the following order types:

- Limit order
"The key feature of this order type is that you  provide a limit price which is the worst price you are willing to trade at. 
When you trade you may get a slightly better price than your limit price, depending on the structure of the book."
Source: https://www.machow.ski/posts/2021-07-18-introduction-to-limit-order-books

- Market order
"A market order is a special order type that does not require you to provide a limit price. 
It is an instruction to buy or sell a certain quantity of shares at any price available. 
If a market Buy order is submitted to the exchange, the exchange will start matching against orders on the 
ask side of the book regardless of the price until the order is filled, or there is no more quantity remaining."
Source: https://www.machow.ski/posts/2021-07-18-introduction-to-limit-order-books

"""


def match_order(
    side: str,
    limit_price: float,
    quantity: float,
    bids: SortedDict,
    asks: SortedDict,
    market_order: bool = False,
) -> tuple[list[tuple[float, float]], float]:
    trades = []

    # Type checking
    if not isinstance(side, str):
        raise TypeError(f"Wrong type for side: {type(side)}")
    if not isinstance(limit_price, (int, float)):
        raise TypeError(f"Wrong type for limit_price: {type(limit_price)}")
    if not isinstance(quantity, (int, float)):
        raise TypeError(f"Wrong type for quantity: {type(quantity)}")
    if not isinstance(bids, SortedDict):
        raise TypeError(f"Wrong type for bids: {type(bids)}")
    if not isinstance(asks, SortedDict):
        raise TypeError(f"Wrong type for asks: {type(asks)}")
    if not isinstance(market_order, bool):
        raise TypeError(f"Wrong type for market_order: {type(market_order)}")

    # Check for valid inputs
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    if not market_order and limit_price < 0:
        raise ValueError("limit_price cannot be negative")

    # Set the book to be used later for the price and quantity
    if side == "buy":
        book = asks
    elif side == "sell":
        book = bids
    else:
        raise TypeError(f"Wrong side: {side}")

    # Match as long as there are orders in the book.
    # Since quantity gets updated in this while loop there should also be a condition,
    # that quantity > 0 to avoid an infinite loop if it reaches 0.
    while book and quantity > 0:
        if side == "buy":
            # Lowest ask is the resting order
            book_price, book_quantity = book.peekitem(0)

            # The limit price is the bid price.
            # bid price (limit price) >= ask price (book price) has to be true
            # It has to be a limit order
            if not market_order and limit_price < book_price:
                break

        elif side == "sell":
            # Highest bid is the resting order
            book_price, book_quantity = book.peekitem(-1)

            # Limit price not aggressive enough to cross the spread. stop matching
            if not market_order and limit_price > book_price:
                break

        # Fill as much as possible at this level, capped by available liquidity
        trade_quantity = min(quantity, book_quantity)

        # Book price gets used for the trade: either lowest ask or highest bid
        trades.append((book_price, trade_quantity))

        # Handle orders that are big (multiple price levels)
        quantity -= trade_quantity

        # Update the book
        if book_quantity == trade_quantity:
            # If book gets depleted by the trade, delete the entry
            del book[book_price]
        else:
            # Handle small orders that only remove part of the offer
            book[book_price] = book_quantity - trade_quantity

    return trades, quantity


# This function removes a limit order from the book that is selected by the "side" argument.
def cancel_limit_order(
    side: str, limit_price: float, quantity: float, bids: SortedDict, asks: SortedDict
) -> None:
    # Type checking
    if not isinstance(side, str):
        raise TypeError(f"Wrong type for side: {type(side)}")
    if not isinstance(limit_price, (int, float)):
        raise TypeError(f"Wrong type for limit_price: {type(limit_price)}")
    if not isinstance(quantity, (int, float)):
        raise TypeError(f"Wrong type for quantity: {type(quantity)}")
    if not isinstance(bids, SortedDict):
        raise TypeError(f"Wrong type for bids: {type(bids)}")
    if not isinstance(asks, SortedDict):
        raise TypeError(f"Wrong type for asks: {type(asks)}")

    # Check for valid inputs
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    if limit_price < 0:
        raise ValueError("limit_price cannot be negative")
    if side not in ["buy", "sell"]:
        raise TypeError(f"Wrong side: {side}. Has to be 'buy' or 'sell'.")

    # Set the book to be used later for the price and quantity
    book = bids if side == "buy" else asks

    # Nothing there to cancel
    if limit_price not in book:
        return

    # Calculate the leftover quantity in the book at the limit_price
    remaining = book[limit_price] - quantity

    if remaining <= 0:
        # level fully pulled
        del book[limit_price]
    else:
        # partial pull: cancel only part of the quantity at this level, leaving the rest
        book[limit_price] = remaining


if __name__ == "__main__":
    # Example usage:

    bids = SortedDict({99: 10, 99.5: 10, 100: 10})
    asks = SortedDict({102: 10, 101.5: 10, 101: 10})

    ##########################################################################
    # Limit order

    side = "sell"
    price = 100
    quantity = 2
    trades, remaining = match_order(side, price, quantity, bids, asks)
    print("Limit order")
    print("Trades: ", trades)

    # Rest the remaining part of the order, add it to the relevant book
    if remaining > 0:
        if side == "buy":
            # get(..., 0) avoids a KeyError
            bids[price] = bids.get(price, 0) + remaining
        if side == "sell":
            asks[price] = asks.get(price, 0) + remaining

    print("Bids: ", bids)
    print("Asks: ", asks)
    print("#" * 40, "\n")

    ##########################################################################
    # Market order

    market_order = True
    side = "buy"
    quantity = 22
    trades, unfilled = match_order(
        side, 0, quantity, bids, asks, market_order=market_order
    )
    print("Market order")
    print("Trades: ", trades)
    print("Unfilled: ", unfilled)
