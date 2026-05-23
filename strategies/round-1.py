import json
from statistics import median, stdev
from typing import List

from datamodel import Order, TradingState


class Trader:
    def run(self, state: TradingState):
        result = {}

        WINDOW = 30
        K_VOL = 5
        MIN_EDGE = 1
        MAX_EDGE = 7
        SKEW_COEF = 3.0

        POSITION_LIMITS = {
            "INTARIAN_PEPPER_ROOT": 80,
            "ASH_COATED_OSMIUM": 80,
        }

        if state.traderData:
            try:
                cache = json.loads(state.traderData)
            except json.JSONDecodeError:
                cache = {}
        else:
            cache = {}

        ### ASH COATED OSMIUM — market-make around rolling median

        osmium_orders: List[Order] = []
        order_depth = state.order_depths["ASH_COATED_OSMIUM"]
        recent_mids = cache.get("osmium_mids", [])

        if order_depth.buy_orders and order_depth.sell_orders:
            best_bid = max(order_depth.buy_orders)
            best_ask = min(order_depth.sell_orders)
            recent_mids.append((best_bid + best_ask) / 2)
            if len(recent_mids) > WINDOW:
                recent_mids = recent_mids[-WINDOW:]

        cache["osmium_mids"] = recent_mids

        if len(recent_mids) == WINDOW:
            fair = median(recent_mids)
            sigma = stdev(recent_mids)
            base_edge = max(MIN_EDGE, min(MAX_EDGE, K_VOL * sigma))

            position = state.position.get("ASH_COATED_OSMIUM", 0)
            L = POSITION_LIMITS["ASH_COATED_OSMIUM"]

            skew = SKEW_COEF * (position / L)
            buy_edge = max(MIN_EDGE, base_edge + skew)
            sell_edge = max(MIN_EDGE, base_edge - skew)

            remaining_buy = max(0, L - position)
            remaining_sell = max(0, L + position)

            best_ask_after = min(order_depth.sell_orders) if order_depth.sell_orders else None
            best_bid_after = max(order_depth.buy_orders) if order_depth.buy_orders else None

            if order_depth.sell_orders:
                best_ask = min(order_depth.sell_orders)
                ask_qty = -order_depth.sell_orders[best_ask]
                if best_ask < fair - buy_edge:
                    take_qty = min(remaining_buy, ask_qty)
                    if take_qty > 0:
                        osmium_orders.append(Order("ASH_COATED_OSMIUM", best_ask, take_qty))
                        remaining_buy -= take_qty
                        if take_qty == ask_qty:
                            remaining_asks = [p for p in order_depth.sell_orders if p > best_ask]
                            best_ask_after = min(remaining_asks) if remaining_asks else None

            if order_depth.buy_orders:
                best_bid = max(order_depth.buy_orders)
                bid_qty = order_depth.buy_orders[best_bid]
                if best_bid > fair + sell_edge:
                    take_qty = min(remaining_sell, bid_qty)
                    if take_qty > 0:
                        osmium_orders.append(Order("ASH_COATED_OSMIUM", best_bid, -take_qty))
                        remaining_sell -= take_qty
                        if take_qty == bid_qty:
                            remaining_bids = [p for p in order_depth.buy_orders if p < best_bid]
                            best_bid_after = max(remaining_bids) if remaining_bids else None

            if remaining_buy > 0 and (
                best_ask_after is None or fair - buy_edge < best_ask_after
            ):
                osmium_orders.append(
                    Order("ASH_COATED_OSMIUM", int(round(fair - buy_edge)), remaining_buy)
                )

            if remaining_sell > 0 and (
                best_bid_after is None or fair + sell_edge >= best_bid_after
            ):
                osmium_orders.append(
                    Order("ASH_COATED_OSMIUM", int(round(fair + sell_edge)), -remaining_sell)
                )

            result["ASH_COATED_OSMIUM"] = osmium_orders

        ### INTARIAN PEPPER ROOT — buy and hold with flash-crash safety

        LONG_WIN = 120
        DRAWDOWN_EXIT = 0.03
        VOL_EXIT = 8.0
        SLOPE_REENTRY = 0.05
        LINEARITY_REENTRY = 1.5
        REENTRY_BARS = 30

        def linreg(ys):
            n = len(ys)
            mean_x = (n - 1) / 2
            mean_y = sum(ys) / n
            num = sum((i - mean_x) * (ys[i] - mean_y) for i in range(n))
            den = sum((i - mean_x) ** 2 for i in range(n))
            slope = num / den if den else 0.0
            intercept = mean_y - slope * mean_x
            resid_var = sum((ys[i] - (slope * i + intercept)) ** 2 for i in range(n)) / n
            return slope, resid_var ** 0.5

        pepper_orders: List[Order] = []
        order_depth = state.order_depths["INTARIAN_PEPPER_ROOT"]
        position = state.position.get("INTARIAN_PEPPER_ROOT", 0)
        L = POSITION_LIMITS["INTARIAN_PEPPER_ROOT"]

        mids = cache.get("pepper_mids", [])
        active = cache.get("pepper_active", True)
        calm_bars = cache.get("pepper_calm_bars", 0)

        if order_depth.buy_orders and order_depth.sell_orders:
            best_bid = max(order_depth.buy_orders)
            best_ask = min(order_depth.sell_orders)
            mids.append((best_bid + best_ask) / 2)
            if len(mids) > LONG_WIN:
                mids = mids[-LONG_WIN:]

        if len(mids) == LONG_WIN:
            slope, resid_std = linreg(mids)
            peak = max(mids)
            drawdown = (peak - mids[-1]) / peak if peak else 0.0
            trend_ok = slope > SLOPE_REENTRY and resid_std < LINEARITY_REENTRY

            if active:
                if drawdown > DRAWDOWN_EXIT or resid_std > VOL_EXIT:
                    active = False
                    calm_bars = 0
            else:
                calm_bars = calm_bars + 1 if trend_ok else 0
                if calm_bars >= REENTRY_BARS:
                    active = True

        cache["pepper_mids"] = mids
        cache["pepper_active"] = active
        cache["pepper_calm_bars"] = calm_bars

        target = L if active else 0
        diff = target - position
        if diff > 0 and order_depth.sell_orders:
            best_ask = min(order_depth.sell_orders)
            ask_qty = -order_depth.sell_orders[best_ask]
            qty = min(diff, ask_qty)
            if qty > 0:
                pepper_orders.append(Order("INTARIAN_PEPPER_ROOT", best_ask, qty))
        elif diff < 0 and order_depth.buy_orders:
            best_bid = max(order_depth.buy_orders)
            bid_qty = order_depth.buy_orders[best_bid]
            qty = min(-diff, bid_qty)
            if qty > 0:
                pepper_orders.append(Order("INTARIAN_PEPPER_ROOT", best_bid, -qty))

        result["INTARIAN_PEPPER_ROOT"] = pepper_orders

        return result, 0, json.dumps(cache)
