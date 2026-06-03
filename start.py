from sortedcontainers import SortedDict

bids = SortedDict({99: 10, 99.5: 10, 100: 10})
asks = SortedDict({102: 10, 101.5: 10, 101: 10})
# bids = SortedDict({})
# asks = SortedDict({})


def match_order(type, limit_price, quantity, bids, asks, market_order=False):
    trades = []

    # Set the book to be used later for the price and quantity
    if type == "buy":
        book = asks
    elif type == "sell":
        book = bids
    else:
        raise TypeError(f"Wrong type: {type}")

    # Match as long as there are orders in the book.
    # Since quantity gets updated in this while loop there should also be a condition,
    # that quantity > 0 to avoid an infinite loop if it reaches 0.
    while book and quantity > 0:
        if type == "buy":
            # Lowest ask is the resting order
            book_price, book_quantity = book.peekitem(0)

            # The limit price is the bid price.
            # bid price (limit price) >= ask price (book price) has to be true
            # It has to be a limit order
            if not market_order and limit_price < book_price:
                break

        elif type == "sell":
            # Highest bid is the resting order
            book_price, book_quantity = book.peekitem(-1)

            if not market_order and limit_price > book_price:
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


# Limit order
"""
The key feature of this order type is that you  provide a limit price which is the worst price you are willing to trade at. 
When you trade you may get a slightly better price than your limit price, depending on the structure of the book.
Source: https://www.machow.ski/posts/2021-07-18-introduction-to-limit-order-books
"""

type = "buy"
# type = "sell"
price = 101
quantity = 2
trades, remaining = match_order(type, price, quantity, bids, asks)
print(trades)

# Rest the remaining part of the order, add it to the relevant book
if remaining > 0:
    if type == "buy":
        # get(..., 0) avoids a KeyError
        bids[price] = bids.get(price, 0) + remaining
    if type == "sell":
        asks[price] = asks.get(price, 0) + remaining
print(bids)
print(asks)
print("#" * 40)


# Market order
"""
A market order is a special order type that does not require you to provide a limit price. 
It is an instruction to buy or sell a certain quantity of shares at any price available. 
If a market Buy order is submitted to the exchange, the exchange will start matching against orders on the 
ask side of the book regardless of the price until the order is filled, or there is no more quantity remaining.
Source: https://www.machow.ski/posts/2021-07-18-introduction-to-limit-order-books
"""

market_order = True
type = "buy"
# type = "sell"
quantity = 22
trades, unfilled = match_order(type, 0, quantity, bids, asks, market_order=market_order)
print(trades)
