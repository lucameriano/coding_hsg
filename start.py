from sortedcontainers import SortedDict

bids = SortedDict({100: 10})
asks = SortedDict({101: 10})


def match_order(type, limit_price, quantity, bids, asks):
    trades = []

    # Set the book to be used later for the price and quantity
    if type == "buy":
        book = asks
    elif type == "sell":
        book = bids
    else:
        raise TypeError(f"Unknown type: {type}")

    # Match as long as there are orders in the book.
    # Since quantity gets updated in this while loop there should also be a condition,
    # that quantity > 0 to avoid an infinite loop if it reaches 0.
    while book and quantity > 0:
        if type == "buy":
            # Lowest ask is the resting order
            book_price, book_quantity = book.peekitem(0)

            # The limit price is the bid price.
            # bid price (limit price) >= ask price (book price) has to be true
            if limit_price < book_price:
                break

        elif type == "sell":
            # Highest bid is the resting order
            book_price, book_quantity = book.peekitem(-1)

            if limit_price > book_price:
                break

        # Trade happens at the lowest demand
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


type = "buy"
price = 101
quantity = 11
trades, remaining = match_order(type, price, quantity, bids, asks)
print(trades)
print(bids.get(price, 0))

# Rest the remaining part of the order, add it to the relevant book
if remaining > 0:
    if type == "buy":
        # get(..., 0) avoids a KeyError
        bids[price] = bids.get(price, 0) + remaining
    if type == "sell":
        asks[price] = asks.get(price, 0) + remaining
print(bids)
print(asks)
