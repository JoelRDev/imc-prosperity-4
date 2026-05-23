# IMC Prosperity 4

## Round 1

Items available for trading:
- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

### Historical Data

![ASH_COATED_OSMIUM price graph](./assets/historical_prices/Round-1/ASH_COATED_OSMIUM.png)

![ASH_COATED_OSMIUM price graph](./assets/historical_prices/Round-1/INTARIAN_PEPPER_ROOT.png)

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

### ASH_COATED_OSMIUM
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

Round 1 results were not stellar, lead by a misunderstanding of the manual trading round.

### Improvements

## Round 2

Items available for trading:
- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

### Historical Data

![ASH_COATED_OSMIUM price graph](./assets/historical_prices/Round-2/ASH_COATED_OSMIUM.png)

![ASH_COATED_OSMIUM price graph](./assets/historical_prices/Round-2/INTARIAN_PEPPER_ROOT.png)