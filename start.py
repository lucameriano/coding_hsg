from sortedcontainers import SortedDict

bids = SortedDict({100: 10})
asks = SortedDict({101: 10})
print(bids)
print(asks)

bids[99] = 10
asks[100] = 10
print(bids)
print(asks)

#######################################################

# Slow:
# Match
# for bid_price, bid_quantity in bids.items():
#     print(bid_price, bid_quantity)
#     for ask_price, ask_quantity in asks.items():
#         print(ask_price, ask_quantity)
#         if bid_price >= ask_price:
#             print("Match found")

#######################################################


# Match incoming order
# Inputs: type, limit_price, quantity, bids, asks
def match_order(type, limit_price, quantity, bids, asks):
    trades = []
    type = "buy"

    if type == "buy":
        book = asks
    elif type == "sell":
        book = bids

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

        # Trade happens and the lowest demand gets exchanged
        trade_quantity = min(quantity, book_quantity)

        # Book price gets used for the trade
        trades.append((book_price, trade_quantity))

        # Now handle orders that are big (multiple price levels)
        quantity -= trade_quantity

        # Update the book
        if book_quantity == trade_quantity:
            del book[book_quantity]
        else:
            # Small orders that only remove part of the offer
            book[book_quantity] = book_quantity - trade_quantity

    return trades, quantity


trades, quantity = match_order("buy", 100, 10, bids, asks)
print(trades)
