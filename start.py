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

trades = []
type = "buy"

if type == "buy":
    book = asks
elif type == "sell":
    book = bids

# Highest bid and lowest ask
bid_price, bid_qty = bids.peekitem(-1)
ask_price, ask_qty = asks.peekitem(0)

# Only the best bid and ask can cross
# Always match top-against-top, and re-check the top after every fill.
# The top crossing is your only signal to continue; the top not crossing is a complete proof that you're done.
if bid_price < ask_price:
    print("No match")

# If the above condition is false, we have a match
# So bid_price >= ask_price
print("Match found")

# Trade happens and the lowest demand gets exchanged
trade_quantity = min(bid_qty, ask_qty)

# Price of the trade depends on who the aggressive and passive order was
