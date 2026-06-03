from sortedcontainers import SortedDict

bids = SortedDict({100: 10})
asks = SortedDict({101: 10})

#######################################################


def match_order(type, limit_price, quantity, bids, asks):
    trades = []

    # Set the book to be used later for the price and quantity
    if type == "buy":
        book = asks
    elif type == "sell":
        book = bids
    else:
        raise TypeError(f"Unknown type: {type}")

    while book:
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


trades, remaining = match_order("buy", 103, 10, bids, asks)
print(trades)
