from sortedcontainers import SortedDict

bids = SortedDict({100: 10})
asks = SortedDict({101: 10})
print(bids)
print(asks)

bids[99] = 10
asks[102] = 10
print(bids)
print(asks)
