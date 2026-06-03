from sortedcontainers import SortedDict

bids = SortedDict({100: 10})
asks = SortedDict({101: 10})
print(bids)
print(asks)

bids[99] = 10
asks[100] = 10
print(bids)
print(asks)

highest_bid = bids.peekitem(-1)
lowest_ask = asks.peekitem(0)
print(highest_bid[0])
print(lowest_ask[0])
print("-" * 40)

for bid_price, bid_quantity in bids.items():
    print(bid_price, bid_quantity)
    for ask_price, ask_quantity in asks.items():
        print(ask_price, ask_quantity)
        if bid_price >= ask_price:
            print("Match found")
