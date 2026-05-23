import json
from math import ceil, floor, sqrt

from datamodel import (
    Order,
    OrderDepth,
    Symbol,
    TradingState,
)


PRODUCTS = [
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "SLEEP_POD_SUEDE",
    "SLEEP_POD_LAMB_WOOL",
    "SLEEP_POD_POLYESTER",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_COTTON",
    "MICROCHIP_CIRCLE",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "MICROCHIP_RECTANGLE",
    "MICROCHIP_TRIANGLE",
    "PEBBLES_XS",
    "PEBBLES_S",
    "PEBBLES_M",
    "PEBBLES_L",
    "PEBBLES_XL",
    "ROBOT_VACUUMING",
    "ROBOT_MOPPING",
    "ROBOT_DISHES",
    "ROBOT_LAUNDRY",
    "ROBOT_IRONING",
    "UV_VISOR_YELLOW",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
    "UV_VISOR_MAGENTA",
    "TRANSLATOR_SPACE_GRAY",
    "TRANSLATOR_ASTRO_BLACK",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_GRAPHITE_MIST",
    "TRANSLATOR_VOID_BLUE",
    "PANEL_1X2",
    "PANEL_2X2",
    "PANEL_1X4",
    "PANEL_2X4",
    "PANEL_4X4",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_MINT",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_GARLIC",
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_VANILLA",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_RASPBERRY",
]

PRODUCT_LIMITS = {product: 10 for product in PRODUCTS}

PEBBLES = [
    "PEBBLES_L",
    "PEBBLES_M",
    "PEBBLES_S",
    "PEBBLES_XL",
    "PEBBLES_XS",
]
PEBBLES_FAIR_SUM = 50_000
PEBBLES_BUY_THRESHOLD = 49_999
PEBBLES_SELL_THRESHOLD = 50_001
MAX_PEBBLES_BASKET_SIZE = 10
PEBBLES_PASSIVE_EDGE = 1.5
PEBBLES_PASSIVE_SIZE = 2
PEBBLES_LEG_IMBALANCE_SKEW = 3.0

JUMP_REVERSAL_PARAMS = {
    "ROBOT_DISHES": {
        "beta": -0.232,
        "threshold": 80,
        "target": 10,
        "edge": 2.0,
        "levels": 2,
    },
    "ROBOT_IRONING": {
        "beta": -0.20,
        "threshold": 40,
        "target": 10,
        "edge": 2.0,
        "levels": 2,
    },
    "OXYGEN_SHAKE_EVENING_BREATH": {
        "beta": -0.20,
        "threshold": 40,
        "target": 10,
        "edge": 2.0,
        "levels": 2,
    },
    "OXYGEN_SHAKE_CHOCOLATE": {
        "beta": -0.20,
        "threshold": 40,
        "target": 10,
        "edge": 2.0,
        "levels": 2,
    },
    "UV_VISOR_RED": {
        "beta": -0.35,
        "threshold": 30,
        "target": 5,
        "edge": 2.0,
        "levels": 2,
    },
    "MICROCHIP_OVAL": {
        "beta": -0.20,
        "threshold": 40,
        "target": 5,
        "edge": 2.0,
        "levels": 2,
    },
    "PANEL_1X2": {
        "beta": -0.35,
        "threshold": 30,
        "target": 5,
        "edge": 2.0,
        "levels": 2,
    },
}
JUMP_DELTA_THRESHOLD = 80
JUMP_EDGE_BUFFER = 2.0
REVERSAL_TARGET_POSITION = 10
MAX_LEVELS_TO_CROSS = 2

# Retuned from the day 2-4 top-of-book data: 75 was too eager on days 2-3,
# while 100 kept the basket signal positive across all three files I tested.
SNACKPACK_BASKET_EDGE = 100
SNACKPACK_BASKET_SIZE = 2
SNACKPACK_BASKET_EMA_ALPHA = 2.0 / 501.0

SNACKPACK = [
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_VANILLA",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_RASPBERRY",
]

ROBOT = [
    "ROBOT_VACUUMING",
    "ROBOT_MOPPING",
    "ROBOT_DISHES",
    "ROBOT_LAUNDRY",
    "ROBOT_IRONING",
]

OXYGEN_SHAKE = [
    "OXYGEN_SHAKE_MORNING_BREATH",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_MINT",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_GARLIC",
]

UV_VISOR = [
    "UV_VISOR_YELLOW",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
    "UV_VISOR_MAGENTA",
]

GALAXY_SOUNDS = [
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
]

# Slow single-name mean reversion candidates found in the historical files.
# These use per-product parameters below rather than the global defaults.
SLOW_MR = [
    "PANEL_2X2",
    "MICROCHIP_TRIANGLE",
    "MICROCHIP_RECTANGLE",
    "UV_VISOR_MAGENTA",
    "GALAXY_SOUNDS_DARK_MATTER",
]

SLOW_MR_PARAMS = {
    "PANEL_2X2": {"entry_z": 2.5, "passive_z": 2.0, "edge": 2.0, "passive_edge": 1.0, "size": 3, "passive_size": 2},
    "MICROCHIP_TRIANGLE": {"entry_z": 2.0, "passive_z": 1.75, "edge": 4.0, "passive_edge": 2.0, "size": 3, "passive_size": 2},
    "MICROCHIP_RECTANGLE": {"entry_z": 2.0, "passive_z": 1.75, "edge": 4.0, "passive_edge": 2.0, "size": 3, "passive_size": 2},
    "UV_VISOR_MAGENTA": {"entry_z": 2.0, "passive_z": 1.75, "edge": 2.0, "passive_edge": 1.0, "size": 2, "passive_size": 1},
    "GALAXY_SOUNDS_DARK_MATTER": {"entry_z": 3.0, "passive_z": 2.0, "edge": 2.0, "passive_edge": 1.0, "size": 3, "passive_size": 1},
}

EMA_PRODUCTS = sorted(set(SNACKPACK + SLOW_MR))

# Pair relative-value trades. fair = EMA(mid_a - mid_b); execution crosses
# ask_a/bid_b or bid_a/ask_b only when the top-of-book pair spread is far
# enough from that EMA fair. Sizes are intentionally modest because of the
# 10-unit per-product position cap and overlap with other modules.
PAIR_RELATIVE_VALUE_ALPHA = 2.0 / 501.0
PAIR_RELATIVE_VALUE_TRADES = [
    # Existing high-conviction pairs.
    {"a": "PEBBLES_M", "b": "PEBBLES_XL", "edge": 150.0, "size": 3},
    {"a": "PEBBLES_XS", "b": "PEBBLES_XL", "edge": 200.0, "size": 1},
    {"a": "MICROCHIP_OVAL", "b": "MICROCHIP_TRIANGLE", "edge": 200.0, "size": 1},
    {"a": "MICROCHIP_OVAL", "b": "MICROCHIP_RECTANGLE", "edge": 200.0, "size": 2},
    {"a": "TRANSLATOR_ASTRO_BLACK", "b": "TRANSLATOR_GRAPHITE_MIST", "edge": 100.0, "size": 2},
    {"a": "SLEEP_POD_POLYESTER", "b": "SLEEP_POD_COTTON", "edge": 300.0, "size": 1},

    # New same-bucket RV pairs found by requiring positive day-by-day PnL
    # on days 2, 3, and 4 under a simple crossing-only simulator.  Sizes are
    # kept at 1 to avoid over-allocating the 10-lot product limits and to let
    # the older modules keep priority when their signals are stronger.
    {"a": "PEBBLES_XS", "b": "PEBBLES_S", "edge": 400.0, "size": 1},
    {"a": "PANEL_2X2", "b": "PANEL_2X4", "edge": 250.0, "size": 1},
    {"a": "TRANSLATOR_ECLIPSE_CHARCOAL", "b": "TRANSLATOR_VOID_BLUE", "edge": 250.0, "size": 1},
    {"a": "ROBOT_VACUUMING", "b": "ROBOT_DISHES", "edge": 200.0, "size": 1},
    {"a": "ROBOT_DISHES", "b": "ROBOT_IRONING", "edge": 200.0, "size": 1},
    {"a": "SLEEP_POD_LAMB_WOOL", "b": "SLEEP_POD_NYLON", "edge": 200.0, "size": 1},
    {"a": "UV_VISOR_AMBER", "b": "UV_VISOR_MAGENTA", "edge": 250.0, "size": 1},
    {"a": "OXYGEN_SHAKE_CHOCOLATE", "b": "OXYGEN_SHAKE_GARLIC", "edge": 150.0, "size": 1},
    {"a": "SNACKPACK_CHOCOLATE", "b": "SNACKPACK_STRAWBERRY", "edge": 200.0, "size": 1},
    {"a": "SNACKPACK_PISTACHIO", "b": "SNACKPACK_RASPBERRY", "edge": 200.0, "size": 1},
    {"a": "PANEL_1X2", "b": "PANEL_2X4", "edge": 100.0, "size": 1},
]

# Additional EMA basket strategies for buckets that showed basket-level
# mean reversion. These run only when none of the legs already has an order.
BUCKET_BASKET_EMA_ALPHA = 2.0 / 501.0
BUCKET_EMA_BASKETS = {
    "ROBOT": {"products": ROBOT, "edge": 200.0, "size": 1},
    "OXYGEN_SHAKE": {"products": OXYGEN_SHAKE, "edge": 200.0, "size": 3},
    "UV_VISOR": {"products": UV_VISOR, "edge": 300.0, "size": 5},
    "GALAXY_SOUNDS": {"products": GALAXY_SOUNDS, "edge": 300.0, "size": 5},
}

SECONDARY_PASSIVE = [
    # Kept only where the passive module had either strong total edge or
    # positive markouts in the tape.  The removed names were still available
    # to bucket/pair modules but no longer get unhedged standalone quotes.
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "GALAXY_SOUNDS_DARK_MATTER",
    "OXYGEN_SHAKE_GARLIC",
    "OXYGEN_SHAKE_MINT",
    "UV_VISOR_YELLOW",
    "UV_VISOR_ORANGE",
    "UV_VISOR_MAGENTA",
]

SECONDARY_SIZE_BY_PRODUCT = {
    "GALAXY_SOUNDS_BLACK_HOLES": 2,
    "OXYGEN_SHAKE_GARLIC": 2,
    "UV_VISOR_ORANGE": 2,
    "UV_VISOR_YELLOW": 2,
    "GALAXY_SOUNDS_SOLAR_WINDS": 1,
    "GALAXY_SOUNDS_PLANETARY_RINGS": 1,
    "OXYGEN_SHAKE_MINT": 1,
    "OXYGEN_SHAKE_MORNING_BREATH": 1,
    "UV_VISOR_MAGENTA": 1,
    "UV_VISOR_AMBER": 1,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 1,
    "GALAXY_SOUNDS_DARK_MATTER": 1,
}

EMA_ALPHA = 2.0 / 501.0
RESIDUAL_VAR_ALPHA = 2.0 / 501.0
INVENTORY_SKEW = 8.0
SNACKPACK_PASSIVE_EDGE = 1.0
SLOW_PASSIVE_EDGE = 1.0
SLOW_AGGRESSIVE_EDGE = 3.0
SNACKPACK_PASSIVE_SIZE = 3
SLOW_PASSIVE_SIZE = 2
SLOW_AGGRESSIVE_SIZE = 3
SOFT_INVENTORY_FRACTION = 0.60
HARD_INVENTORY_FRACTION = 0.85
SECONDARY_PASSIVE_SIZE = 1
SECONDARY_PASSIVE_EDGE = 4.0
SECONDARY_PASSIVE_MIN_SPREAD = 8
SECONDARY_PASSIVE_SOFT_CAP = 4
SECONDARY_MICRO_DEV_WEIGHT = 0.6


class Trader:
    def mid_price(self, order_depth: OrderDepth) -> float | None:
        if not order_depth.buy_orders or not order_depth.sell_orders:
            return None

        return (max(order_depth.buy_orders) + min(order_depth.sell_orders)) / 2

    def best_bid(self, order_depth: OrderDepth) -> int | None:
        if not order_depth.buy_orders:
            return None
        return max(order_depth.buy_orders)

    def best_ask(self, order_depth: OrderDepth) -> int | None:
        if not order_depth.sell_orders:
            return None
        return min(order_depth.sell_orders)

    def microprice(self, order_depth: OrderDepth) -> float | None:
        bid = self.best_bid(order_depth)
        ask = self.best_ask(order_depth)
        if bid is None or ask is None:
            return None

        bid_volume = order_depth.buy_orders[bid]
        ask_volume = -order_depth.sell_orders[ask]
        total_volume = bid_volume + ask_volume
        if total_volume <= 0:
            return None

        return (ask * bid_volume + bid * ask_volume) / total_volume

    def crossing_order(
        self,
        product: str,
        order_depth: OrderDepth,
        position: int,
        target: int,
    ) -> list[Order]:
        delta = target - position
        if delta == 0:
            return []

        if delta > 0:
            if not order_depth.sell_orders:
                return []
            return [Order(product, max(order_depth.sell_orders), delta)]

        if not order_depth.buy_orders:
            return []
        return [Order(product, min(order_depth.buy_orders), delta)]

    def add_target_order(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        product: str,
        target: int,
    ) -> None:
        order_depth = state.order_depths.get(product)
        if order_depth is None:
            return

        orders = self.crossing_order(
            product,
            order_depth,
            state.position.get(product, 0),
            max(-PRODUCT_LIMITS[product], min(PRODUCT_LIMITS[product], target)),
        )
        if orders:
            result.setdefault(product, []).extend(orders)

    def add_top_of_book_order(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        product: str,
        quantity: int,
    ) -> None:
        if quantity == 0:
            return

        order_depth = state.order_depths.get(product)
        if order_depth is None:
            return

        position = state.position.get(product, 0)
        if quantity > 0:
            ask = self.best_ask(order_depth)
            if ask is None:
                return
            quantity = min(quantity, PRODUCT_LIMITS[product] - position)
            if quantity > 0:
                result.setdefault(product, []).append(Order(product, ask, quantity))
        else:
            bid = self.best_bid(order_depth)
            if bid is None:
                return
            quantity = -min(-quantity, PRODUCT_LIMITS[product] + position)
            if quantity < 0:
                result.setdefault(product, []).append(Order(product, bid, quantity))

    def trade_pebbles(self, result: dict[Symbol, list[Order]], state: TradingState) -> bool:
        if any(product not in state.order_depths for product in PEBBLES):
            return False

        bids = []
        asks = []
        bid_volumes = []
        ask_volumes = []
        for product in PEBBLES:
            order_depth = state.order_depths[product]
            bid = self.best_bid(order_depth)
            ask = self.best_ask(order_depth)
            if bid is None or ask is None:
                return False
            bids.append(bid)
            asks.append(ask)
            bid_volumes.append(order_depth.buy_orders[bid])
            ask_volumes.append(-order_depth.sell_orders[ask])

        sum_bid = sum(bids)
        sum_ask = sum(asks)

        if sum_ask <= PEBBLES_BUY_THRESHOLD:
            quantity = min(
                MAX_PEBBLES_BASKET_SIZE,
                min(ask_volumes),
                min(PRODUCT_LIMITS[product] - state.position.get(product, 0) for product in PEBBLES),
            )
            for product in PEBBLES:
                self.add_top_of_book_order(result, state, product, quantity)
            return quantity > 0
        elif sum_bid >= PEBBLES_SELL_THRESHOLD:
            quantity = min(
                MAX_PEBBLES_BASKET_SIZE,
                min(bid_volumes),
                min(PRODUCT_LIMITS[product] + state.position.get(product, 0) for product in PEBBLES),
            )
            for product in PEBBLES:
                self.add_top_of_book_order(result, state, product, -quantity)
            return quantity > 0

        return False

    def trade_pebbles_passive(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        mids: dict[str, float],
    ) -> None:
        if any(result.get(product) for product in PEBBLES):
            return

        if any(product not in state.order_depths or product not in mids for product in PEBBLES):
            return

        mid_sum = sum(mids[product] for product in PEBBLES)
        residual = PEBBLES_FAIR_SUM - mid_sum
        average_position = sum(state.position.get(product, 0) for product in PEBBLES) / len(PEBBLES)

        if average_position > 6:
            passive_buy_size = 0
            passive_sell_size = 5
        elif average_position < -6:
            passive_buy_size = 5
            passive_sell_size = 0
        else:
            passive_buy_size = PEBBLES_PASSIVE_SIZE
            passive_sell_size = PEBBLES_PASSIVE_SIZE

        buy_quantity = min(
            passive_buy_size,
            min(PRODUCT_LIMITS[product] - state.position.get(product, 0) for product in PEBBLES),
        )
        sell_quantity = min(
            passive_sell_size,
            min(PRODUCT_LIMITS[product] + state.position.get(product, 0) for product in PEBBLES),
        )

        buy_orders = []
        sell_orders = []
        for product in PEBBLES:
            order_depth = state.order_depths[product]
            bid = self.best_bid(order_depth)
            ask = self.best_ask(order_depth)
            if bid is None or ask is None:
                return
            if ask - bid < 4:
                return

            leg_position = state.position.get(product, 0)
            leg_imbalance = leg_position - average_position
            fair = mids[product] + residual / len(PEBBLES)
            fair -= PEBBLES_LEG_IMBALANCE_SKEW * leg_imbalance / PRODUCT_LIMITS[product]
            fair -= INVENTORY_SKEW * leg_position / PRODUCT_LIMITS[product]
            bid_quote = min(bid + 1, floor(fair - PEBBLES_PASSIVE_EDGE))
            ask_quote = max(ask - 1, ceil(fair + PEBBLES_PASSIVE_EDGE))

            if buy_quantity > 0 and bid_quote < ask and leg_position < SOFT_INVENTORY_FRACTION * PRODUCT_LIMITS[product]:
                buy_orders.append(Order(product, bid_quote, buy_quantity))
            if sell_quantity > 0 and ask_quote > bid and leg_position > -SOFT_INVENTORY_FRACTION * PRODUCT_LIMITS[product]:
                sell_orders.append(Order(product, ask_quote, -sell_quantity))

        if buy_quantity > 0 and len(buy_orders) == len(PEBBLES):
            for order in buy_orders:
                result.setdefault(order.symbol, []).append(order)
        if sell_quantity > 0 and len(sell_orders) == len(PEBBLES):
            for order in sell_orders:
                result.setdefault(order.symbol, []).append(order)

    def update_mid_cache(self, cache: dict, state: TradingState) -> dict[str, float]:
        prev_mids = cache.setdefault("prev_mids", {})
        current_mids = {}
        for product, order_depth in state.order_depths.items():
            mid = self.mid_price(order_depth)
            if mid is not None:
                current_mids[product] = mid
        cache["current_mids"] = current_mids
        return prev_mids

    def update_ema_stats(
        self,
        cache: dict,
        mids: dict[str, float],
    ) -> dict[str, dict[str, float]]:
        ema_state = cache.setdefault("ema", {})
        var_state = cache.setdefault("resid_var", {})
        sample_state = cache.setdefault("ema_samples", {})
        stats = {}

        for product in EMA_PRODUCTS:
            mid = mids.get(product)
            if mid is None:
                continue

            previous_ema = float(ema_state.get(product, mid))
            ema = previous_ema + EMA_ALPHA * (mid - previous_ema)
            residual = mid - ema
            previous_var = float(var_state.get(product, residual * residual))
            resid_var = (1.0 - RESIDUAL_VAR_ALPHA) * previous_var + RESIDUAL_VAR_ALPHA * (
                residual * residual
            )

            ema_state[product] = round(ema, 4)
            var_state[product] = round(resid_var, 4)
            sample_state[product] = int(sample_state.get(product, 0)) + 1
            stats[product] = {
                "ema": ema,
                "std": max(1.0, sqrt(resid_var)),
                "samples": sample_state[product],
            }

        return stats

    def trade_jump_reversal(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        prev_mids: dict[str, float],
    ) -> None:
        for product, params in JUMP_REVERSAL_PARAMS.items():
            if result.get(product):
                continue

            beta = params["beta"]
            threshold = params.get("threshold", JUMP_DELTA_THRESHOLD)
            edge = params.get("edge", JUMP_EDGE_BUFFER)
            target_size = params.get("target", REVERSAL_TARGET_POSITION)
            max_levels = params.get("levels", MAX_LEVELS_TO_CROSS)
            order_depth = state.order_depths.get(product)
            if order_depth is None or product not in prev_mids:
                continue

            mid = self.mid_price(order_depth)
            bid = self.best_bid(order_depth)
            ask = self.best_ask(order_depth)
            if mid is None or bid is None or ask is None:
                continue

            delta = mid - prev_mids[product]
            if abs(delta) < threshold:
                continue

            fair = mid + beta * delta
            position = state.position.get(product, 0)
            target = -target_size if delta > 0 else target_size
            desired_quantity = target - position

            if desired_quantity > 0:
                quantity = min(desired_quantity, PRODUCT_LIMITS[product] - position)
                executable_quantity = 0
                limit_price = None
                for price in sorted(order_depth.sell_orders)[:max_levels]:
                    if fair - price < edge:
                        break
                    level_quantity = -order_depth.sell_orders[price]
                    executable_quantity += min(level_quantity, quantity - executable_quantity)
                    limit_price = price
                    if executable_quantity >= quantity:
                        break
                if executable_quantity > 0 and limit_price is not None:
                    result.setdefault(product, []).append(Order(product, limit_price, executable_quantity))
            elif desired_quantity < 0:
                quantity = min(-desired_quantity, PRODUCT_LIMITS[product] + position)
                executable_quantity = 0
                limit_price = None
                for price in sorted(order_depth.buy_orders, reverse=True)[:max_levels]:
                    if price - fair < edge:
                        break
                    level_quantity = order_depth.buy_orders[price]
                    executable_quantity += min(level_quantity, quantity - executable_quantity)
                    limit_price = price
                    if executable_quantity >= quantity:
                        break
                if executable_quantity > 0 and limit_price is not None:
                    result.setdefault(product, []).append(Order(product, limit_price, -executable_quantity))

    def trade_snackpack_basket(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        cache: dict,
        mids: dict[str, float],
    ) -> None:
        if any(result.get(product) for product in SNACKPACK):
            return
        if any(product not in state.order_depths or product not in mids for product in SNACKPACK):
            return

        bids = []
        asks = []
        bid_volumes = []
        ask_volumes = []
        for product in SNACKPACK:
            order_depth = state.order_depths[product]
            bid = self.best_bid(order_depth)
            ask = self.best_ask(order_depth)
            if bid is None or ask is None:
                return
            bids.append(bid)
            asks.append(ask)
            bid_volumes.append(order_depth.buy_orders[bid])
            ask_volumes.append(-order_depth.sell_orders[ask])

        basket_mid = sum(mids[product] for product in SNACKPACK)
        previous_fair = float(cache.get("snackpack_basket_ema", basket_mid))
        basket_fair = previous_fair + SNACKPACK_BASKET_EMA_ALPHA * (basket_mid - previous_fair)
        cache["snackpack_basket_ema"] = round(basket_fair, 4)

        sum_bid = sum(bids)
        sum_ask = sum(asks)
        if sum_ask < basket_fair - SNACKPACK_BASKET_EDGE:
            quantity = min(
                SNACKPACK_BASKET_SIZE,
                min(ask_volumes),
                min(PRODUCT_LIMITS[product] - state.position.get(product, 0) for product in SNACKPACK),
            )
            if quantity <= 0:
                return
            for product in SNACKPACK:
                self.add_top_of_book_order(result, state, product, quantity)
        elif sum_bid > basket_fair + SNACKPACK_BASKET_EDGE:
            quantity = min(
                SNACKPACK_BASKET_SIZE,
                min(bid_volumes),
                min(PRODUCT_LIMITS[product] + state.position.get(product, 0) for product in SNACKPACK),
            )
            if quantity <= 0:
                return
            for product in SNACKPACK:
                self.add_top_of_book_order(result, state, product, -quantity)

    def trade_pair_relative_value(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        cache: dict,
        mids: dict[str, float],
    ) -> None:
        pair_ema_state = cache.setdefault("pair_rv_ema", {})

        for params in PAIR_RELATIVE_VALUE_TRADES:
            product_a = params["a"]
            product_b = params["b"]
            order_depth_a = state.order_depths.get(product_a)
            order_depth_b = state.order_depths.get(product_b)
            if (
                order_depth_a is None
                or order_depth_b is None
                or product_a not in mids
                or product_b not in mids
            ):
                continue

            bid_a = self.best_bid(order_depth_a)
            ask_a = self.best_ask(order_depth_a)
            bid_b = self.best_bid(order_depth_b)
            ask_b = self.best_ask(order_depth_b)
            if bid_a is None or ask_a is None or bid_b is None or ask_b is None:
                continue

            pair_key = product_a + "|" + product_b
            spread_mid = mids[product_a] - mids[product_b]
            previous_fair = float(pair_ema_state.get(pair_key, spread_mid))
            fair = previous_fair + PAIR_RELATIVE_VALUE_ALPHA * (spread_mid - previous_fair)
            pair_ema_state[pair_key] = round(fair, 4)

            # Do not stack a relative-value trade on top of an existing order from
            # a higher-priority strategy in the same product during this tick.
            if result.get(product_a) or result.get(product_b):
                continue

            edge = float(params["edge"])
            max_size = int(params["size"])
            position_a = state.position.get(product_a, 0)
            position_b = state.position.get(product_b, 0)

            # Product A is cheap versus product B: buy A at A's ask and sell B at B's bid.
            buy_a_sell_b_spread = ask_a - bid_b
            if buy_a_sell_b_spread < fair - edge:
                quantity = min(
                    max_size,
                    -order_depth_a.sell_orders[ask_a],
                    order_depth_b.buy_orders[bid_b],
                    PRODUCT_LIMITS[product_a] - position_a,
                    PRODUCT_LIMITS[product_b] + position_b,
                )
                if quantity > 0:
                    result.setdefault(product_a, []).append(Order(product_a, ask_a, quantity))
                    result.setdefault(product_b, []).append(Order(product_b, bid_b, -quantity))
                continue

            # Product A is rich versus product B: sell A at A's bid and buy B at B's ask.
            sell_a_buy_b_spread = bid_a - ask_b
            if sell_a_buy_b_spread > fair + edge:
                quantity = min(
                    max_size,
                    order_depth_a.buy_orders[bid_a],
                    -order_depth_b.sell_orders[ask_b],
                    PRODUCT_LIMITS[product_a] + position_a,
                    PRODUCT_LIMITS[product_b] - position_b,
                )
                if quantity > 0:
                    result.setdefault(product_a, []).append(Order(product_a, bid_a, -quantity))
                    result.setdefault(product_b, []).append(Order(product_b, ask_b, quantity))

    def trade_bucket_ema_baskets(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        cache: dict,
        mids: dict[str, float],
    ) -> None:
        basket_ema_state = cache.setdefault("bucket_basket_ema", {})

        for basket_name, params in BUCKET_EMA_BASKETS.items():
            products = params["products"]
            if any(product not in state.order_depths or product not in mids for product in products):
                continue

            bids = []
            asks = []
            bid_volumes = []
            ask_volumes = []
            complete_book = True
            for product in products:
                order_depth = state.order_depths[product]
                bid = self.best_bid(order_depth)
                ask = self.best_ask(order_depth)
                if bid is None or ask is None:
                    complete_book = False
                    break
                bids.append(bid)
                asks.append(ask)
                bid_volumes.append(order_depth.buy_orders[bid])
                ask_volumes.append(-order_depth.sell_orders[ask])

            if not complete_book:
                continue

            basket_mid = sum(mids[product] for product in products)
            previous_fair = float(basket_ema_state.get(basket_name, basket_mid))
            basket_fair = previous_fair + BUCKET_BASKET_EMA_ALPHA * (basket_mid - previous_fair)
            basket_ema_state[basket_name] = round(basket_fair, 4)

            # Keep this as a clean bucket trade: if another module already wants
            # one leg, skip the entire bucket rather than mixing inventories.
            if any(result.get(product) for product in products):
                continue

            edge = float(params["edge"])
            basket_size = int(params["size"])
            sum_bid = sum(bids)
            sum_ask = sum(asks)

            if sum_ask < basket_fair - edge:
                quantity = min(
                    basket_size,
                    min(ask_volumes),
                    min(PRODUCT_LIMITS[product] - state.position.get(product, 0) for product in products),
                )
                if quantity <= 0:
                    continue
                for product, ask in zip(products, asks):
                    result.setdefault(product, []).append(Order(product, ask, quantity))

            elif sum_bid > basket_fair + edge:
                quantity = min(
                    basket_size,
                    min(bid_volumes),
                    min(PRODUCT_LIMITS[product] + state.position.get(product, 0) for product in products),
                )
                if quantity <= 0:
                    continue
                for product, bid in zip(products, bids):
                    result.setdefault(product, []).append(Order(product, bid, -quantity))

    def add_passive_quote(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        product: str,
        fair: float,
        min_edge: float,
        quote_size: int,
        *,
        allow_bid_signal: bool = True,
        allow_ask_signal: bool = True,
        min_spread: int = 4,
    ) -> None:
        if result.get(product):
            return

        order_depth = state.order_depths.get(product)
        if order_depth is None:
            return

        bid = self.best_bid(order_depth)
        ask = self.best_ask(order_depth)
        if bid is None or ask is None:
            return
        if ask - bid < min_spread:
            return

        limit = PRODUCT_LIMITS[product]
        position = state.position.get(product, 0)
        fair_adjusted = fair - INVENTORY_SKEW * position / limit
        bid_quote = bid + 1
        ask_quote = ask - 1

        can_bid = position < SOFT_INVENTORY_FRACTION * limit
        can_ask = position > -SOFT_INVENTORY_FRACTION * limit
        if position > HARD_INVENTORY_FRACTION * limit:
            can_bid = False
            can_ask = True
        elif position < -HARD_INVENTORY_FRACTION * limit:
            can_bid = True
            can_ask = False

        can_bid = can_bid and allow_bid_signal
        can_ask = can_ask and allow_ask_signal

        if can_bid and bid_quote < ask and fair_adjusted - bid_quote >= min_edge:
            quantity = min(quote_size, limit - position)
            if quantity > 0:
                result.setdefault(product, []).append(Order(product, bid_quote, quantity))

        if can_ask and ask_quote > bid and ask_quote - fair_adjusted >= min_edge:
            quantity = min(quote_size, limit + position)
            if quantity > 0:
                result.setdefault(product, []).append(Order(product, ask_quote, -quantity))

    def trade_snackpack_market_making(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        mids: dict[str, float],
        ema_stats: dict[str, dict[str, float]],
    ) -> None:
        for product in SNACKPACK:
            order_depth = state.order_depths.get(product)
            stats = ema_stats.get(product)
            if order_depth is None or product not in mids or stats is None:
                continue

            microprice = self.microprice(order_depth)
            if microprice is None:
                continue

            mid = mids[product]
            micro_dev = microprice - mid
            fair = stats["ema"] + micro_dev
            z = (mid - stats["ema"]) / stats["std"] if stats["samples"] >= 20 else 0.0
            allow_bid = z < -1.5 or fair > mid
            allow_ask = z > 1.5 or fair < mid

            self.add_passive_quote(
                result,
                state,
                product,
                fair,
                SNACKPACK_PASSIVE_EDGE,
                SNACKPACK_PASSIVE_SIZE,
                allow_bid_signal=allow_bid,
                allow_ask_signal=allow_ask,
            )

    def trade_secondary_passive_market_making(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        mids: dict[str, float],
    ) -> None:
        for product in SECONDARY_PASSIVE:
            order_depth = state.order_depths.get(product)
            if order_depth is None or product not in mids:
                continue

            microprice = self.microprice(order_depth)
            if microprice is None:
                continue

            mid = mids[product]
            micro_dev = microprice - mid
            fair = mid + SECONDARY_MICRO_DEV_WEIGHT * micro_dev
            position = state.position.get(product, 0)

            self.add_passive_quote(
                result,
                state,
                product,
                fair,
                SECONDARY_PASSIVE_EDGE,
                SECONDARY_SIZE_BY_PRODUCT.get(product, SECONDARY_PASSIVE_SIZE),
                allow_bid_signal=position < SECONDARY_PASSIVE_SOFT_CAP,
                allow_ask_signal=position > -SECONDARY_PASSIVE_SOFT_CAP,
                min_spread=SECONDARY_PASSIVE_MIN_SPREAD,
            )

    def trade_slow_mean_reversion(
        self,
        result: dict[Symbol, list[Order]],
        state: TradingState,
        mids: dict[str, float],
        ema_stats: dict[str, dict[str, float]],
    ) -> None:
        for product in SLOW_MR:
            if result.get(product):
                continue

            order_depth = state.order_depths.get(product)
            stats = ema_stats.get(product)
            if order_depth is None or product not in mids or stats is None or stats["samples"] < 20:
                continue

            bid = self.best_bid(order_depth)
            ask = self.best_ask(order_depth)
            if bid is None or ask is None:
                continue

            params = SLOW_MR_PARAMS.get(product, {})
            entry_z = float(params.get("entry_z", 2.5))
            passive_z = float(params.get("passive_z", 2.0))
            aggressive_edge = float(params.get("edge", SLOW_AGGRESSIVE_EDGE))
            passive_edge = float(params.get("passive_edge", SLOW_PASSIVE_EDGE))
            aggressive_size = int(params.get("size", SLOW_AGGRESSIVE_SIZE))
            passive_size = int(params.get("passive_size", SLOW_PASSIVE_SIZE))

            mid = mids[product]
            fair = stats["ema"]
            z = (mid - fair) / stats["std"]
            position = state.position.get(product, 0)

            if z < -entry_z and fair - ask > aggressive_edge:
                quantity = min(
                    aggressive_size,
                    -order_depth.sell_orders[ask],
                    PRODUCT_LIMITS[product] - position,
                )
                self.add_top_of_book_order(result, state, product, quantity)
                continue

            if z > entry_z and bid - fair > aggressive_edge:
                quantity = min(
                    aggressive_size,
                    order_depth.buy_orders[bid],
                    PRODUCT_LIMITS[product] + position,
                )
                self.add_top_of_book_order(result, state, product, -quantity)
                continue

            self.add_passive_quote(
                result,
                state,
                product,
                fair,
                passive_edge,
                passive_size,
                allow_bid_signal=z < -passive_z,
                allow_ask_signal=z > passive_z,
            )

    def run(self, state: TradingState):
        if state.traderData:
            try:
                cache = json.loads(state.traderData)
            except json.JSONDecodeError:
                cache = {}
        else:
            cache = {}

        result = {}
        prev_mids = self.update_mid_cache(cache, state)
        current_mids = cache.get("current_mids", {})
        ema_stats = self.update_ema_stats(cache, current_mids)

        self.trade_pebbles(result, state)
        self.trade_jump_reversal(result, state, prev_mids)
        self.trade_pair_relative_value(result, state, cache, current_mids)
        self.trade_pebbles_passive(result, state, current_mids)
        self.trade_snackpack_basket(result, state, cache, current_mids)
        self.trade_bucket_ema_baskets(result, state, cache, current_mids)
        self.trade_snackpack_market_making(result, state, current_mids, ema_stats)
        self.trade_slow_mean_reversion(result, state, current_mids, ema_stats)
        self.trade_secondary_passive_market_making(result, state, current_mids)

        cache["prev_mids"] = cache.get("current_mids", {})
        cache.pop("current_mids", None)
        conversions = 0
        trader_data = json.dumps(cache, separators=(",", ":"))
        return result, conversions, trader_data
