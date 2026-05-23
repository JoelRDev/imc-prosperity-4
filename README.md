WORK IN PROGRESS

# IMC Prosperity 4

## Round 1

Items available for trading:
- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Position limits:
- `ASH_COATED_OSMIUM: 80`
- `INTARIAN_PEPPER_ROOT: 80`

### Historical Data

![ASH_COATED_OSMIUM price graph](./assets/historical_prices/Round-1/ASH_COATED_OSMIUM.png)

![INTARIAN_PEPPER_ROOT price graph](./assets/historical_prices/Round-1/INTARIAN_PEPPER_ROOT.png)

### Discussion

Other than a brief encounter with setting up the datamodel and trader classes for Round 0 (tutorial round), this was my first experience of digesting price data and creating a Python algorithm intended to trade it profitably.

I very much appreciated IMC not making Round 1 too complex and allowing the new participants to practice on something easier. It became clear that there were two main patterns that I needed to identify: `ASH_COATED_OSMIUM` was mean-reverting and `INTARIAN_PEPPER_ROOT` followed a mostly linear pattern.

My strategy for this round was therefore simple:
### `INTARIAN_PEPPER_ROOT` 
This asset utilized a long-biased buy-and-hold strategy with crash protection. At this point of the competition I was not sure whether regime change was going to be a factor that we had to be prepared for. Therefore, the strategy initially would blindly buy until the 80-unit long limit. The downside protection solution was to fit rolling 120 mid-prices into a linear trend and exit the position to zero if drawdown from the window exceeded 3% (allowing for minor price fluctuations since the trend was not "perfectly" linear). 

Another exit mechanism was to consider volatility. I theorized that a major regime change could be preceded by an increase in volatility, which could allow me to get out of the position before hitting my "stop-loss strategy". Therefore if residual volatility exceeded 8.0 the position would also be exited.

Re-entry criteria were set at:
```
slope > 0.05
resid_std < 1.5
```
The purpose of this implementation was to ensure that the position would only be re-entered during calm, upward trending periods in the market.

### `ASH_COATED_OSMIUM`
This asset was the more meaningful learning experience from Round 1. As seen from the price graph, `ASH_COATED_OSMIUM` was a mean-reverting asset. This meant that it tended to fluctuate around `price = 10,000`.

My first thought was to very simply go long and clear short inventory at prices below 10,000 and to go short and clear long inventory at prices above 10,000. There were several considerations that lead me to learn a lot about how mean-reverting assets are traded at a basic level:
- How do we decide what the "fair value" (mean-reverting target in this case) of the asset was? 10,000 is arbitrary in the sense that we cannot guarantee it does not change. Even if it looks right, can we just trust our vision and approximation to say the fair value really is 10,000? What about 10,050 or 9,950?
- Logically, the most profitable strategy will not be to go max long at 9,999 and max short at 10,001. While the mean-reverting nature suggests this could be a profitable strategy, we are leaving money on the table. Simply put, selling for a profit of 2 is less than selling for a profit of 100.
- If I have determined the point at which I want to start buying or selling, how can I try to guarantee that I do not max out my position limits in case the price continues to drift in that direction. If the price is at 9900 and my long inventory is maxed out, if the price drifts below 9900 I have no more buying power, meaning I cannot lock in these positions far from the mean.

In hindsight, these considerations were important throughout the competition. Mean-reverting assets were a consideration in every single round from this point onwards, having a good understanding was paramount.

My algorithm addressed these considerations with the following strategies:
The `ASH_COATED_OSMIUM` algorithm is a rolling-median market maker. It stores the last 30 mid-prices, uses their median as fair value, and quotes around that fair value. The quote edge is volatility-scaled with K_VOL = 5, bounded between 1 and 7. Inventory is managed with a skew: if the bot is long, it makes buys less attractive and sells more attractive; if short, the reverse. It also crosses obviously mispriced top-of-book orders before placing passive quotes.

### Results

![Round 1 results](./assets/results/Round1_Results.png)

Round 1 results were less than stellar, lead by a misunderstanding of the manual trading round.

## Round 2

Items available for trading:
- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Position limits:
- `ASH_COATED_OSMIUM: 80`
- `INTARIAN_PEPPER_ROOT: 80`

### Historical Data

![ASH_COATED_OSMIUM price graph](./assets/historical_prices/Round-2/ASH_COATED_OSMIUM.png)

![INTARIAN_PEPPER_ROOT price graph](./assets/historical_prices/Round-2/INTARIAN_PEPPER_ROOT.png)

### Discussion

The most valuable information we were given in Round 2 was that our assumptions from Round 1 had held. We got an extra day of trading data and the patterns had not changed, `ASH_COATED_OSMIUM` was still exhibiting its mean-reversion around 10,000 and `INTARIAN_PEPPER_ROOT` was continuing its linear climb up. This meant that the algorithms did not have to be reinvented, only adjusted. The wiki mentioned "The products `INTARIAN_PEPPER_ROOT` and `ASH_COATED_OSMIUM` are the same", giving the necessary indication that regime change would likely not be a major concern. My placement in the previous round however told me there were plenty of profits left on the table, there was work to do.

One new opportunity was given to us. In Round 2, teams could bid for extra quotes in the order book. My initial thinking was that expanding the size of the order book could be beneficial, after all, more participants in the market would allow me to get my market-making positions filled more quickly. Upon further inspection however, it became clear that this would not be worth the cost.

By introducing more players into the market, spreads were likely to decrease as market-making participants would want to quote around the fair value to get their trades filled. A decrease in spreads meant less profitable trades, I therefore decided to bid 0 and to continue refining my existing algorithms.

### `ASH_COATED_OSMIUM`

The algorithm keeps the 30-tick rolling median fair value but separates volatility estimation into a longer 245-tick window. It also improves execution by sweeping multiple profitable book levels instead of only checking the best bid/ask. A position-reducing quote at fair value is added when inventory exceeds half the limit, helping unload risk without waiting for the normal edge quotes.

### `INTARIAN_PEPPER_ROOT`

The same long-with-safety logic remains, but re-entry is faster: REENTRY_BARS drops from 30 to 10. The aim was still to hold the upward-drifting product most of the time, while stepping aside during flash-crash or high-volatility regimes.

### Results

![Round 2 results](./assets/results/Round2_Results.png)

These results were promising. My algorithm had improved and my manual trading performance was very good. I cleared the `200,000 XIREC` threshold for qualifying for Round 3, where the leaderboard would reset.

## Round 3

Items available for trading:
- `HYDROGEL_PACK`
- `VELVETFRUIT_EXTRACT`
- `VEV_4000`
- `VEV_4500`
- `VEV_5000`
- `VEV_5100`
- `VEV_5200`
- `VEV_5300`
- `VEV_5400`
- `VEV_5500`
- `VEV_6000`
- `VEV_6500`

The voucher values represent the strike price of the options contract. Time to expiration at the beginning of the historical data was 8 days, therefore for the simulation round TTE would be set at 5 days.

Position limits:
- `HYDROGEL_PACK: 200`
- `VELVETFRUIT_EXTRACT: 200`
- `VEV_4000: 300`
- `VEV_4500: 300`
- `VEV_5000: 300`
- `VEV_5100: 300`
- `VEV_5200: 300`
- `VEV_5300: 300`
- `VEV_5400: 300`
- `VEV_5500: 300`
- `VEV_6000: 300`
- `VEV_6500: 300`

### Historical Data

![HYDROGEL_PACK price graph](./assets/historical_prices/Round-3/HYDROGEL_PACK.png)

![VELVETFRUIT_EXTRACT price graph](./assets/historical_prices/Round-3/VELVETFRUIT_EXTRACT.png)

![Combined vouchers price graphs](./assets/historical_prices/Round-3/COMBINED_VOUCHERS.png)

### Discussion

The most important takeaways from the historical price data in this round:
- Trends appear to be mean-reverting
- Higher strike prices (more OTM) have higher volatility but consistent directional movements with the other vouchers (following `VELVETFRUIT_EXTRACT`)
- Volume seems to be decreasing as strike prices get more OTM

### Strategy

Round 3 uses a common strategy for all tradable assets. It can still be best described as an anchored market maker. For each product, the algorithm keeps a 30-tick rolling mid-price cache and uses the median of those mids as the market-derived fair value. This market fair value is then blended with an anchor. The important change from the earlier version is that the anchor weight is no longer the same for every product.

The fair value is:
```
fair = (1 - anchor_weight) * rolling_median + anchor_weight * anchor
```
The configured fixed anchors are:
```
HYDROGEL_PACK = 10000
VELVETFRUIT_EXTRACT = 5250
VEV_4000 = 1260
VEV_4500 = 755
VEV_5000 = 265
VEV_5100 = 170
VEV_5200 = 97
VEV_5300 = 46
VEV_5400 = 15
VEV_5500 = 6
```
`VEV_6000` and `VEV_6500` have position limits but no fixed anchors.

Since the `VEV` products were options contracts with the strike price included in the name, I also added a simple Black-Scholes pricing component. The algorithm uses `VELVETFRUIT_EXTRACT` as the underlying, parses the strike from the voucher name, and calculates implied volatility from the available voucher mid-prices. It then takes the median implied volatility across the vouchers and uses that to create an IV-based anchor for each `VEV` product. Time to expiry is modeled with:
```
INITIAL_TTE_DAYS = 5
DAYS_PER_YEAR = 365
```
For vouchers with both a fixed anchor and an IV anchor, the final anchor is:
```
anchor = 0.75 * fixed_anchor + 0.25 * iv_anchor
```
If a voucher has no fixed anchor, as is the case for `VEV_6000` and `VEV_6500`, the IV anchor can be used on its own when it is available. Otherwise, the product falls back to the rolling median.

The quote edge is volatility-based, but it also takes the current spread into account. It uses half of the current spread plus the standard deviation of the 30 recent mids multiplied by `k_vol`, then clips this between the product's `min_edge` and `max_edge`:
```
base_edge = half_spread + k_vol * stdev(recent_mids)
```

The product-specific parameters are:
```
HYDROGEL_PACK: anchor_weight = 0.20, k_vol = 8.0, min_edge = 4.0, max_edge = 10.0, skew_coef = 3.0
VELVETFRUIT_EXTRACT: anchor_weight = 0.35, k_vol = 5.0, min_edge = 1.0, max_edge = 7.0, skew_coef = 3.0
VEV_4000: anchor_weight = 0.40, k_vol = 5.0, min_edge = 1.0, max_edge = 6.0, skew_coef = 2.0
VEV_4500: anchor_weight = 0.40, k_vol = 5.0, min_edge = 1.0, max_edge = 4.0, skew_coef = 3.5
VEV_5000: anchor_weight = 0.45, k_vol = 5.0, min_edge = 1.0, max_edge = 4.0, skew_coef = 4.5
VEV_5100: anchor_weight = 0.45, k_vol = 5.0, min_edge = 1.0, max_edge = 4.0, skew_coef = 5.0
VEV_5200: anchor_weight = 0.45, k_vol = 5.0, min_edge = 1.0, max_edge = 2.0, skew_coef = 6.0
VEV_5300: anchor_weight = 0.50, k_vol = 5.0, min_edge = 1.0, max_edge = 2.0, skew_coef = 6.0
VEV_5400: anchor_weight = 0.50, k_vol = 5.0, min_edge = 1.0, max_edge = 2.0, skew_coef = 6.0
VEV_5500: anchor_weight = 0.50, k_vol = 5.0, min_edge = 1.0, max_edge = 2.0, skew_coef = 6.0
VEV_6000: anchor_weight = 0.50, k_vol = 5.0, min_edge = 1.0, max_edge = 2.0, skew_coef = 6.0
VEV_6500: anchor_weight = 0.50, k_vol = 5.0, min_edge = 1.0, max_edge = 2.0, skew_coef = 6.0
```

Execution has three layers:

- It aggressively buys asks below fair - buy_edge.
- It aggressively sells bids above fair + sell_edge.
- It places passive bid/ask quotes at rounded fair-minus-edge and fair-plus-edge if capacity remains.

Inventory is managed by skewing edges with each product's `skew_coef`. A long position widens the buy edge and tightens the sell edge, encouraging selling; a short position does the opposite. If absolute inventory exceeds half the limit, it also places a position-reducing order at rounded fair value when possible.

### Results

![Round 3 results](./assets/results/Round3_Results.png)

These results were very promising, my algorithm had worked as intended and I was in a good position going into round 4.

## Round 4