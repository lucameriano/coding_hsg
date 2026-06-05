import numpy as np
from sortedcontainers import SortedDict
import matplotlib.pyplot as plt
from start import match_order, cancel_limit_order


# Define how the price for the order creation gets chosen


# def generate_price(
#     type,
#     bids,
#     asks,
#     ref,
#     expectation,
# ):
#     if type == "buy":
#         anchor = bids.peekitem(-1)[0] if bids else ref  # best bid
#         anchor *= 1.0001
#     elif type == "sell":
#         anchor = asks.peekitem(0)[0] if asks else ref  # best ask
#         anchor *= 0.9999
#     else:
#         raise TypeError(f"Wrong type: {type}")

#     # Random price round it to 2 digits to keep orderbook not too fragmented
#     random_price = round(anchor * (1 + expectation), 2)

#     # Add outliers
#     # outlier = np.abs(expectation) > 0.0005
#     outlier = True
#     if outlier:
#         random_price = round(anchor * (1 + expectation) ** 2, 2)

#     return random_price


def generate_price(type, bids, asks, ref, expectation):
    TICK = 0.05
    #   offset < 0  -> improves/crosses the quote (keeps spread tight, things trade)
    #   offset > 0  -> rests behind the touch (builds the hump)
    offset = np.random.normal(loc=1 * TICK, scale=20.0 * TICK)

    if type == "buy":
        anchor = bids.peekitem(-1)[0] if bids else ref
        return round(anchor * (1 + expectation) - offset, 2)
    elif type == "sell":
        anchor = asks.peekitem(0)[0] if asks else ref
        return round(anchor * (1 + expectation) + offset, 2)
    else:
        raise TypeError(f"Wrong type: {type}")


# Starting order book
bids = SortedDict({99: 100, 99.5: 100, 100: 100})
asks = SortedDict({102: 100, 101.5: 100, 100.05: 100})
np.random.seed(100)

# Starting midprice
best_bid = bids.peekitem(-1)[0]
best_ask = asks.peekitem(0)[0]

# Starting reference price = mid-price, which is (best bid + best ask) / 2
# The reference price is used for the price used when creating or cancelling orders
ref0 = (best_bid + best_ask) / 2
decisions = 150_000

# Define the available participant choices and their probabilities
choices = [
    "nothing",
    "buy_limit",
    "sell_limit",
    "buy_market",
    "sell_market",
    "cancel_buy_limit",
    "cancel_sell_limit",
]
probability_weights = np.array([0.5, 0.25, 0.25, 0.19, 0.19, 0.07, 0.07])
probabilities = np.random.rand(decisions, len(probability_weights))
probabilities = probabilities + probability_weights * 0.9

# Pregenerate randomness
action_choices = np.argmax(probabilities, axis=1)

# OLD
# quantities = np.random.uniform(1, 2, size=decisions)

# realistic right tail of occasional large orders
quantities = np.random.lognormal(mean=2.6, sigma=0.8, size=decisions)

# Generate an expectation for the participant
# This expectation represents the change in the fair value that the participant expects in the future
expectations = np.random.normal(0, 0.0005, size=decisions)
# around 2% are outliers
outliers = np.random.rand(decisions) < np.random.normal(0.02, 0.0005, size=decisions)
expectations[outliers] = np.random.normal(0, 0.0008, size=outliers.sum())


# Create the lists for the simulation
refs = [ref0]
trades_combined = []

for i in range(decisions):
    # The reference price is now the current mid-price
    # Use the best bid and asks to compute the mid-price if available
    # else use the last ref price. refs[i-1] will always be available since current ref gets appended to refs.
    if bids and asks:
        best_bid = bids.peekitem(-1)[0]
        best_ask = asks.peekitem(0)[0]
        ref = (best_bid + best_ask) / 2
    # else:
    #     # ref = refs[i - 1]
    #     ref = ref0
    refs.append(ref)

    # Choose an action
    choice = choices[action_choices[i]]

    # Get a quantity for the action
    quantity = quantities[i]

    # Get the expectation
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
        price = np.random.choice(list(bids.keys())[:5]) if bids else ref
        cancel_limit_order("buy", price, quantity, bids, asks)
        trades = []

    elif choice == "cancel_sell_limit":
        # Cancel a random ask price. If asks is empty use reference price
        price = np.random.choice(list(asks.keys())[-5:]) if asks else ref
        cancel_limit_order("sell", price, quantity, bids, asks)
        trades = []

    trades_combined.append(trades)


prices = [p for trades in trades_combined for (p, q) in trades]
plt.plot(prices)
plt.show()


import numpy as np
import matplotlib

matplotlib.use("Agg")  # file output; drop this line to view interactively


def run_sim(decisions=150_000, seed=100, snap_every=2000):
    bids = SortedDict({99: 30, 99.5: 30, 100: 30})
    asks = SortedDict({102: 30, 101.5: 30, 101: 30})
    np.random.seed(seed)

    ref = (bids.peekitem(-1)[0] + asks.peekitem(0)[0]) / 2

    choices = [
        "nothing",
        "buy_limit",
        "sell_limit",
        "buy_market",
        "sell_market",
        "cancel_buy_limit",
        "cancel_sell_limit",
    ]

    # recorders
    mids = np.empty(decisions)
    spreads = np.empty(decisions)
    trade_prices = []
    n_limit = n_crossed = 0  # how often a "limit" order is marketable
    n_empty = 0  # how often a book side was empty
    depth_snaps = []  # (mid, [(price,qty)...] for bids+asks)

    last_mid = ref
    for i in range(decisions):
        if bids and asks:
            best_bid = bids.peekitem(-1)[0]
            best_ask = asks.peekitem(0)[0]
            ref = (best_bid + best_ask) / 2
            spreads[i] = best_ask - best_bid
            last_mid = ref
        else:
            n_empty += 1
            spreads[i] = np.nan
        mids[i] = last_mid

        choice = choices[action_choices[i]]
        quantity = quantities[i]
        expectation = expectations[i]

        if choice == "nothing":
            trades = []
        elif choice == "buy_limit":
            price = generate_price("buy", bids, asks, ref, expectation)
            trades, remaining = match_order("buy", price, quantity, bids, asks)
            n_limit += 1
            if trades:
                n_crossed += 1
            if remaining > 0:
                bids[price] = bids.get(price, 0) + remaining
        elif choice == "sell_limit":
            price = generate_price("sell", bids, asks, ref, expectation)
            trades, remaining = match_order("sell", price, quantity, bids, asks)
            n_limit += 1
            if trades:
                n_crossed += 1
            if remaining > 0:
                asks[price] = asks.get(price, 0) + remaining
        elif choice == "buy_market":
            trades, _ = match_order("buy", 0, quantity, bids, asks, market_order=True)
        elif choice == "sell_market":
            trades, _ = match_order("sell", 0, quantity, bids, asks, market_order=True)
        elif choice == "cancel_buy_limit":
            # Cancel a random bid price. If bids is empty use reference price
            price = np.random.choice(list(bids.keys())[:5]) if bids else ref
            cancel_limit_order("buy", price, quantity, bids, asks)
            trades = []

        elif choice == "cancel_sell_limit":
            # Cancel a random ask price. If asks is empty use reference price
            price = np.random.choice(list(asks.keys())[-5:]) if asks else ref
            cancel_limit_order("sell", price, quantity, bids, asks)
            trades = []

        trade_prices.extend(p for (p, q) in trades)

        if i % snap_every == 0 and bids and asks:
            mid_now = (bids.peekitem(-1)[0] + asks.peekitem(0)[0]) / 2
            snap = [("bid", p, q) for p, q in bids.items()] + [
                ("ask", p, q) for p, q in asks.items()
            ]
            depth_snaps.append((mid_now, snap))

    return dict(
        mids=mids,
        spreads=spreads,
        trade_prices=np.array(trade_prices),
        n_limit=n_limit,
        n_crossed=n_crossed,
        n_empty=n_empty,
        depth_snaps=depth_snaps,
        decisions=decisions,
    )


# ----------------------------------------------------------------------------- stats
def acf(x, nlags):
    x = np.asarray(x, float)
    x = x - x.mean()
    n = len(x)
    denom = np.dot(x, x)
    return np.array(
        [
            1.0 if denom == 0 else np.dot(x[: n - k], x[k:]) / denom
            for k in range(nlags + 1)
        ]
    )


def analyze(res, sample_every=25, plot_path="diagnostic.png"):
    mids = res["mids"]
    spreads = res["spreads"]

    # returns on a coarse-grained event clock
    m = mids[::sample_every]
    r = np.diff(np.log(m))
    r = r[np.isfinite(r)]
    mu, sd = r.mean(), r.std()
    skew = np.mean(((r - mu) / sd) ** 3)
    exkurt = np.mean(((r - mu) / sd) ** 4) - 3

    r_acf = acf(r, 30)
    abs_acf = acf(np.abs(r), 30)

    # diffusion: Var(mid[t+tau]-mid[t]) vs tau   (slope ~1 => random walk)
    taus = np.unique(np.geomspace(1, len(m) // 4, 25).astype(int))
    dvar = np.array([np.var(m[t:] - m[:-t]) for t in taus])
    ok = dvar > 0
    diff_exp = np.polyfit(np.log(taus[ok]), np.log(dvar[ok]), 1)[0]

    # drift of this one path
    t = np.arange(len(mids))
    slope = np.polyfit(t, mids, 1)[0]

    sp = spreads[np.isfinite(spreads)]
    cross_frac = res["n_crossed"] / max(res["n_limit"], 1)

    # average book depth vs distance from mid
    bin_w, max_d = 0.25, 8.0
    edges = np.arange(0, max_d + bin_w, bin_w)
    vol = np.zeros(len(edges) - 1)
    cnt = 0
    for mid_now, snap in res["depth_snaps"]:
        cnt += 1
        for side, p, q in snap:
            d = abs(p - mid_now)
            j = int(d // bin_w)
            if 0 <= j < len(vol):
                vol[j] += q
    depth = vol / max(cnt, 1)
    centers = edges[:-1] + bin_w / 2

    # ---------------- print summary
    print("=" * 64)
    print(
        f"events: {res['decisions']:,}   returns sampled every {sample_every} events "
        f"(n={len(r):,})"
    )
    print("-" * 64)
    print(
        f"path drift (slope of mid vs event)  : {slope:+.2e}  "
        f"[one seed; rerun seeds to confirm ~0]"
    )
    print(f"diffusion exponent  (1.0 = RW)      : {diff_exp:.3f}")
    print(f"return mean / std                   : {mu:+.2e} / {sd:.2e}")
    print(f"return skew                         : {skew:+.3f}")
    print(
        f"return EXCESS KURTOSIS (0 = normal) : {exkurt:+.3f}   "
        f"{'<- fat tails' if exkurt > 1 else '<- ~Gaussian tails'}"
    )
    print(
        f"return ACF  lag1/2/5                 : "
        f"{r_acf[1]:+.3f} / {r_acf[2]:+.3f} / {r_acf[5]:+.3f}"
    )
    print(
        f"|return| ACF lag1/5/10/25            : "
        f"{abs_acf[1]:+.3f} / {abs_acf[5]:+.3f} / {abs_acf[10]:+.3f} / {abs_acf[25]:+.3f}   "
        f"{'<- clustering' if abs_acf[5] > 0.05 else '<- no clustering'}"
    )
    print(
        f"spread  mean / median / max         : "
        f"{np.nanmean(sp):.3f} / {np.nanmedian(sp):.3f} / {np.nanmax(sp):.3f}"
    )
    print(f"'limit' orders that cross the book  : {cross_frac * 100:.2f}%")
    print(f"book-side-empty events              : {res['n_empty']}")
    print("=" * 64)

    # ---------------- plots
    fig, ax = plt.subplots(3, 3, figsize=(16, 11))

    ax[0, 0].plot(mids, lw=0.6)
    ax[0, 0].set_title("mid price path")

    ax[0, 1].plot(spreads, lw=0.4)
    ax[0, 1].set_title(f"spread over time (median {np.nanmedian(sp):.2f})")

    ax[0, 2].plot(centers, depth, marker="o", ms=3)
    ax[0, 2].set_title(
        "avg depth vs distance from mid\n(real books: hump a few ticks out)"
    )
    ax[0, 2].set_xlabel("distance from mid")
    ax[0, 2].set_ylabel("avg volume")

    # return histogram, log-y, with matched normal
    ax[1, 0].hist(r, bins=120, density=True, alpha=0.6)
    xs = np.linspace(r.min(), r.max(), 400)
    ax[1, 0].plot(
        xs,
        np.exp(-0.5 * ((xs - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
        "r-",
        lw=1.2,
        label="matched normal",
    )
    ax[1, 0].set_yscale("log")
    ax[1, 0].legend()
    ax[1, 0].set_title(f"return dist (excess kurtosis {exkurt:+.2f})")

    ax[1, 1].bar(range(1, 31), r_acf[1:], width=0.8)
    ax[1, 1].axhline(0, color="k", lw=0.5)
    ax[1, 1].set_title("return ACF  (want ~0)")

    ax[1, 2].bar(range(1, 31), abs_acf[1:], width=0.8)
    ax[1, 2].axhline(0, color="k", lw=0.5)
    ax[1, 2].set_title("|return| ACF  (decay = vol clustering)")

    ax[2, 0].loglog(taus, dvar, marker="o", ms=3, label="empirical")
    ax[2, 0].loglog(taus, dvar[0] * (taus / taus[0]), "r--", label="slope 1 (RW)")
    ax[2, 0].set_title(f"diffusion: Var vs lag (exp {diff_exp:.2f})")
    ax[2, 0].set_xlabel("lag (samples)")
    ax[2, 0].legend()

    ax[2, 1].hist(sp, bins=60, density=True, alpha=0.7)
    ax[2, 1].set_title("spread distribution")

    ax[2, 2].axis("off")
    ax[2, 2].text(
        0.0,
        0.95,
        f"excess kurtosis : {exkurt:+.2f}\n"
        f"diffusion exp   : {diff_exp:.2f}\n"
        f"return ACF(1)   : {r_acf[1]:+.3f}\n"
        f"|ret| ACF(5)    : {abs_acf[5]:+.3f}\n"
        f"median spread   : {np.nanmedian(sp):.2f}\n"
        f"limit-cross %   : {cross_frac * 100:.2f}%",
        family="monospace",
        va="top",
        fontsize=12,
    )

    fig.tight_layout()
    fig.savefig(plot_path, dpi=110)
    print(f"saved plots -> {plot_path}")


if __name__ == "__main__":
    res = run_sim(decisions=150_000, seed=100)
    analyze(res, sample_every=25, plot_path="diagnostic.png")
