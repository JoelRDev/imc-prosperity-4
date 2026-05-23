import json
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


class Trader:
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
        vol_window: int = 245,
        k_vol: float = 5.0,
        min_edge: float = 1.0,
        max_edge: float = 7.0,
        skew_coef: float = 3.0,
    ) -> List[Order]:
        """Market-make around a rolling-median fair value, optionally pulled toward an anchor."""
        orders: List[Order] = []
        recent_mids = cache.get(f"{cache_prefix}_mids", [])
        vol_mids = cache.get(f"{cache_prefix}_vol_mids", [])

        if not order_depth or not order_depth.buy_orders or not order_depth.sell_orders:
            cache[f"{cache_prefix}_mids"] = recent_mids
            cache[f"{cache_prefix}_vol_mids"] = vol_mids
            return orders

        best_bid = max(order_depth.buy_orders)
        best_ask = min(order_depth.sell_orders)
        mid = (best_bid + best_ask) / 2

        recent_mids.append(mid)
        if len(recent_mids) > window:
            recent_mids = recent_mids[-window:]
        vol_mids.append(mid)
        if len(vol_mids) > vol_window:
            vol_mids = vol_mids[-vol_window:]

        cache[f"{cache_prefix}_mids"] = recent_mids
        cache[f"{cache_prefix}_vol_mids"] = vol_mids

        if len(recent_mids) < window or len(vol_mids) < 2:
            return orders

        fair = median(recent_mids)
        if anchor is not None and anchor_weight > 0:
            fair = (1 - anchor_weight) * fair + anchor_weight * anchor

        sigma = stdev(vol_mids)
        base_edge = max(min_edge, min(max_edge, k_vol * sigma))

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

    def run(self, state: TradingState):
        result = {}

        POSITION_LIMITS = {
            "HYDROGEL_PACK": 200,
            "VELVETFRUIT_EXTRACT": 200,
            "VELVETFRUIT_EXTRACT_VOUCHER": 300,
        }

        if state.traderData:
            try:
                cache = json.loads(state.traderData)
            except json.JSONDecodeError:
                cache = {}
        else:
            cache = {}

        ### HYDROGEL_PACK

        result["HYDROGEL_PACK"] = self.anchored_market_make(
            product="HYDROGEL_PACK",
            order_depth=state.order_depths.get("HYDROGEL_PACK"),
            position=state.position.get("HYDROGEL_PACK", 0),
            limit=POSITION_LIMITS["HYDROGEL_PACK"],
            cache=cache,
            cache_prefix="hydrogel",
            anchor=10000,
            anchor_weight=0.3,
        )

        ### VELVETFRUIT_EXTRACT

        trader_data = json.dumps(cache)
        conversions = 0
        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data


## To Run Backtester --> ./bt round-3/round-3-ai.py 3 --out backtests/latest_backtest.log --merge-pnl