import json
from math import erf, exp, log, sqrt
from statistics import median, stdev
from typing import Any, List

from datamodel import (
    Listing,
    Observation,
    Order,
    OrderDepth,
    ProsperityEncoder,
    Symbol,
    Trade,
    TradingState,
)


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(
        self,
        state: TradingState,
        orders: dict[Symbol, list[Order]],
        conversions: int,
        trader_data: str,
    ) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])
        return compressed

    def compress_order_depths(
        self, order_depths: dict[Symbol, OrderDepth]
    ) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]
        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )
        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                getattr(observation, "sugarPrice", 0),
                getattr(observation, "sunlightIndex", 0),
            ]
        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])
        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[: max_length - 3] + "..."


logger = Logger()


PRODUCT_LIMITS = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300,
    "VEV_4500": 300,
    "VEV_5000": 300,
    "VEV_5100": 300,
    "VEV_5200": 300,
    "VEV_5300": 300,
    "VEV_5400": 300,
    "VEV_5500": 300,
    "VEV_6000": 300,
    "VEV_6500": 300,
}

PRODUCT_ANCHORS = {
    "HYDROGEL_PACK": 10000,
    "VELVETFRUIT_EXTRACT": 5250,
    "VEV_4000": 1260,
    "VEV_4500": 755,
    "VEV_5000": 265,
    "VEV_5100": 170,
    "VEV_5200": 97,
    "VEV_5300": 46,
    "VEV_5400": 15,
    "VEV_5500": 6
}

PRODUCT_MM_PARAMS = {
    "HYDROGEL_PACK": {
        "anchor_weight": 0.2,
        "window": 30,
        "k_vol": 8.0,
        "min_edge": 4.0,
        "max_edge": 10.0,
        "skew_coef": 3.0,
    },
    "VELVETFRUIT_EXTRACT": {
        "anchor_weight": 0.35,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 7.0,
        "skew_coef": 3.0,
    },
    "VEV_4000": {
        "anchor_weight": 0.40,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 6.0,
        "skew_coef": 2,
    },
    "VEV_4500": {
        "anchor_weight": 0.40,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 4.0,
        "skew_coef": 3.5,
    },
    "VEV_5000": {
        "anchor_weight": 0.45,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 4.0,
        "skew_coef": 4.5,
    },
    "VEV_5100": {
        "anchor_weight": 0.45,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 4.0,
        "skew_coef": 5.0,
    },
    "VEV_5200": {
        "anchor_weight": 0.45,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 2.0,
        "skew_coef": 6.0,
    },
    "VEV_5300": {
        "anchor_weight": 0.50,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 2.0,
        "skew_coef": 6.0,
    },
    "VEV_5400": {
        "anchor_weight": 0.50,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 2.0,
        "skew_coef": 6.0,
    },
    "VEV_5500": {
        "anchor_weight": 0.50,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 2.0,
        "skew_coef": 6.0,
    },
    "VEV_6000": {
        "anchor_weight": 0.50,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 2.0,
        "skew_coef": 6.0,
    },
    "VEV_6500": {
        "anchor_weight": 0.50,
        "window": 30,
        "k_vol": 5.0,
        "min_edge": 1.0,
        "max_edge": 2.0,
        "skew_coef": 6.0,
    },
}

UNDERLYING = "VELVETFRUIT_EXTRACT"
INITIAL_TTE_DAYS = 5
DAYS_PER_YEAR = 365
VEV_IV_BLEND = 0.25


class Trader:
    def norm_cdf(self, x: float) -> float:
        return 0.5 * (1 + erf(x / sqrt(2)))

    def bs_call_price(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        rate: float = 0.0,
    ) -> float:
        if time_to_expiry <= 0 or volatility <= 0:
            return max(spot - strike, 0)

        vol_sqrt_t = volatility * sqrt(time_to_expiry)
        d1 = (
            log(spot / strike)
            + (rate + 0.5 * volatility**2) * time_to_expiry
        ) / vol_sqrt_t
        d2 = d1 - vol_sqrt_t
        discounted_strike = strike * exp(-rate * time_to_expiry)
        return spot * self.norm_cdf(d1) - discounted_strike * self.norm_cdf(d2)

    def implied_volatility_call(
        self,
        price: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        rate: float = 0.0,
    ) -> float | None:
        intrinsic = max(spot - strike * exp(-rate * time_to_expiry), 0)

        if (
            time_to_expiry <= 0
            or spot <= 0
            or strike <= 0
            or price <= intrinsic
            or price >= spot
        ):
            return None

        low, high = 1e-6, 5.0
        for _ in range(60):
            mid = (low + high) / 2
            model_price = self.bs_call_price(spot, strike, time_to_expiry, mid, rate)
            if model_price < price:
                low = mid
            else:
                high = mid

        return (low + high) / 2

    def current_mid(self, order_depth: OrderDepth | None) -> float | None:
        if not order_depth or not order_depth.buy_orders or not order_depth.sell_orders:
            return None

        return (max(order_depth.buy_orders) + min(order_depth.sell_orders)) / 2

    def vev_strike(self, product: str) -> float | None:
        if not product.startswith("VEV_"):
            return None

        try:
            return float(product.split("_", 1)[1])
        except ValueError:
            return None

    def vev_iv_anchors(self, state: TradingState) -> dict[str, float]:
        spot = self.current_mid(state.order_depths.get(UNDERLYING))
        if spot is None:
            return {}

        time_to_expiry = max(
            (INITIAL_TTE_DAYS - state.timestamp / 1_000_000) / DAYS_PER_YEAR,
            1e-6,
        )
        implied_vols: list[float] = []

        for product in PRODUCT_LIMITS:
            strike = self.vev_strike(product)
            mid = self.current_mid(state.order_depths.get(product))
            if strike is None or mid is None:
                continue

            iv = self.implied_volatility_call(mid, spot, strike, time_to_expiry)
            if iv is not None:
                implied_vols.append(iv)

        if not implied_vols:
            return {}

        cross_section_iv = median(implied_vols)
        anchors = {}
        for product in PRODUCT_LIMITS:
            strike = self.vev_strike(product)
            if strike is None:
                continue

            anchors[product] = self.bs_call_price(
                spot=spot,
                strike=strike,
                time_to_expiry=time_to_expiry,
                volatility=cross_section_iv,
            )

        return anchors

    def market_make_around_fair(
        self,
        product: str,
        order_depth: OrderDepth,
        position: int,
        limit: int,
        fair: float,
        base_edge: float,
        *,
        min_edge: float = 1.0,
        skew_coef: float = 3.0,
    ) -> List[Order]:
        orders: List[Order] = []

        skew = skew_coef * (position / limit)
        buy_edge = max(min_edge, base_edge + skew)
        sell_edge = max(min_edge, base_edge - skew)

        remaining_buy = max(0, limit - position)
        remaining_sell = max(0, limit + position)

        best_ask_after = None
        for price in sorted(order_depth.sell_orders):
            avail = -order_depth.sell_orders[price]
            if price >= fair - buy_edge or remaining_buy <= 0:
                best_ask_after = price
                break
            take = min(remaining_buy, avail)
            orders.append(Order(product, price, take))
            remaining_buy -= take
            if take < avail:
                best_ask_after = price
                break

        best_bid_after = None
        for price in sorted(order_depth.buy_orders, reverse=True):
            avail = order_depth.buy_orders[price]
            if price <= fair + sell_edge or remaining_sell <= 0:
                best_bid_after = price
                break
            take = min(remaining_sell, avail)
            orders.append(Order(product, price, -take))
            remaining_sell -= take
            if take < avail:
                best_bid_after = price
                break

        reduce_buy = reduce_sell = False
        if abs(position) > limit // 2:
            fair_int = int(round(fair))
            if position > 0 and fair_int != int(round(fair + sell_edge)):
                qty = min(position, remaining_sell)
                if qty > 0 and (best_bid_after is None or fair_int > best_bid_after):
                    orders.append(Order(product, fair_int, -qty))
                    remaining_sell -= qty
                    reduce_sell = True
            elif position < 0 and fair_int != int(round(fair - buy_edge)):
                qty = min(-position, remaining_buy)
                if qty > 0 and (best_ask_after is None or fair_int < best_ask_after):
                    orders.append(Order(product, fair_int, qty))
                    remaining_buy -= qty
                    reduce_buy = True

        if remaining_buy > 0 and not reduce_buy and (
            best_ask_after is None or fair - buy_edge < best_ask_after
        ):
            orders.append(Order(product, int(round(fair - buy_edge)), remaining_buy))

        if remaining_sell > 0 and not reduce_sell and (
            best_bid_after is None or fair + sell_edge >= best_bid_after
        ):
            orders.append(Order(product, int(round(fair + sell_edge)), -remaining_sell))

        return orders

    def anchored_market_make(
        self,
        product: str,
        order_depth: OrderDepth,
        position: int,
        limit: int,
        cache: dict,
        cache_prefix: str,
        *,
        anchor: float | None = None,
        anchor_weight: float = 0.0,
        window: int = 30,
        k_vol: float = 5.0,
        min_edge: float = 1.0,
        max_edge: float = 7.0,
        skew_coef: float = 3.0,
    ) -> List[Order]:
        """Market-make around a rolling-median fair value, optionally pulled toward an anchor."""
        orders: List[Order] = []
        recent_mids = cache.get(f"{cache_prefix}_mids", [])

        if not order_depth or not order_depth.buy_orders or not order_depth.sell_orders:
            cache[f"{cache_prefix}_mids"] = recent_mids
            return orders

        best_bid = max(order_depth.buy_orders)
        best_ask = min(order_depth.sell_orders)
        mid = (best_bid + best_ask) / 2

        recent_mids.append(mid)
        if len(recent_mids) > window:
            recent_mids = recent_mids[-window:]

        cache[f"{cache_prefix}_mids"] = recent_mids

        if len(recent_mids) < window:
            return orders

        fair = median(recent_mids)
        if anchor is not None and anchor_weight > 0:
            fair = (1 - anchor_weight) * fair + anchor_weight * anchor

        half_spread = (best_ask - best_bid) / 2
        volatility_buffer = k_vol * stdev(recent_mids)
        base_edge = max(min_edge, min(max_edge, half_spread + volatility_buffer))

        return self.market_make_around_fair(
            product=product,
            order_depth=order_depth,
            position=position,
            limit=limit,
            fair=fair,
            base_edge=base_edge,
            min_edge=min_edge,
            skew_coef=skew_coef,
        )

    def run(self, state: TradingState):
        result = {}

        if state.traderData:
            try:
                cache = json.loads(state.traderData)
            except json.JSONDecodeError:
                cache = {}
        else:
            cache = {}

        iv_anchors = self.vev_iv_anchors(state)

        for product, limit in PRODUCT_LIMITS.items():
            if product not in state.order_depths:
                continue

            params = PRODUCT_MM_PARAMS[product]
            fixed_anchor = PRODUCT_ANCHORS.get(product)
            iv_anchor = iv_anchors.get(product)
            if fixed_anchor is not None and iv_anchor is not None:
                anchor = (1 - VEV_IV_BLEND) * fixed_anchor + VEV_IV_BLEND * iv_anchor
            elif iv_anchor is not None:
                anchor = iv_anchor
            else:
                anchor = fixed_anchor

            result[product] = self.anchored_market_make(
                product=product,
                order_depth=state.order_depths.get(product),
                position=state.position.get(product, 0),
                limit=limit,
                cache=cache,
                cache_prefix=product.lower(),
                anchor=anchor,
                anchor_weight=params["anchor_weight"],
                window=params["window"],
                k_vol=params["k_vol"],
                min_edge=params["min_edge"],
                max_edge=params["max_edge"],
                skew_coef=params["skew_coef"],
            )

        trader_data = json.dumps(cache)
        conversions = 0
        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data


## To Run Backtester --> prosperity4btest cli round-3-copy.py 3 --out latest_backlog.log --merge-pnl