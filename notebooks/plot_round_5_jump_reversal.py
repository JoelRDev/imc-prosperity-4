from __future__ import annotations

from collections import defaultdict
from csv import DictReader
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


JUMP_REVERSAL_PARAMS = {
    "ROBOT_DISHES": {"beta": -0.232, "threshold": 80, "target": 10},
    "ROBOT_IRONING": {"beta": -0.20, "threshold": 40, "target": 10},
    "OXYGEN_SHAKE_EVENING_BREATH": {"beta": -0.20, "threshold": 40, "target": 10},
    "OXYGEN_SHAKE_CHOCOLATE": {"beta": -0.20, "threshold": 40, "target": 10},
    "UV_VISOR_RED": {"beta": -0.35, "threshold": 30, "target": 5},
    "MICROCHIP_OVAL": {"beta": -0.20, "threshold": 40, "target": 5},
    "PANEL_1X2": {"beta": -0.35, "threshold": 30, "target": 5},
}

TIMESTAMPS_PER_DAY = 1_000_000
WINDOW_BEFORE = 5
WINDOW_AFTER = 8


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "data" / "Round-5").is_dir() and (candidate / "assets").is_dir():
            return candidate
    raise FileNotFoundError("Could not find repo root")


def load_round_5_trade_prices(root: Path) -> dict[str, list[dict[str, float]]]:
    weighted_prices: dict[tuple[str, int, int], list[float]] = defaultdict(lambda: [0.0, 0.0])

    for path in sorted((root / "data" / "Round-5").glob("trades_round_5_day_*.csv")):
        day = int(path.stem.split("_")[-1])
        with path.open(newline="") as handle:
            for row in DictReader(handle, delimiter=";"):
                product = row["symbol"]
                if product not in JUMP_REVERSAL_PARAMS:
                    continue

                price = float(row["price"])
                quantity = int(row["quantity"])
                key = (product, day, int(row["timestamp"]))
                weighted_prices[key][0] += price * quantity
                weighted_prices[key][1] += quantity

    by_product: dict[str, list[dict[str, float]]] = defaultdict(list)
    for (product, day, timestamp), (notional, quantity) in weighted_prices.items():
        if quantity == 0:
            continue
        by_product[product].append(
            {
                "day": day,
                "timestamp": timestamp,
                "global_t": (day - 2) * TIMESTAMPS_PER_DAY + timestamp,
                "price": notional / quantity,
            }
        )

    for product in by_product:
        by_product[product].sort(key=lambda point: (point["day"], point["timestamp"]))

    return by_product


def detect_events(by_product: dict[str, list[dict[str, float]]]) -> list[dict[str, float]]:
    events = []
    for product, series in by_product.items():
        threshold = JUMP_REVERSAL_PARAMS[product]["threshold"]
        for index in range(1, len(series) - WINDOW_AFTER):
            delta = series[index]["price"] - series[index - 1]["price"]
            if abs(delta) < threshold or index < WINDOW_BEFORE:
                continue
            direction = 1 if delta > 0 else -1
            next_delta = series[index + 1]["price"] - series[index]["price"]
            path = [
                direction * (series[offset]["price"] - series[index]["price"])
                for offset in range(index - WINDOW_BEFORE, index + WINDOW_AFTER + 1)
            ]
            events.append(
                {
                    "product": product,
                    "index": index,
                    "day": series[index]["day"],
                    "timestamp": series[index]["timestamp"],
                    "delta": delta,
                    "direction": direction,
                    "next_delta": next_delta,
                    "reversed_next": -delta * next_delta > 0,
                    "path": path,
                }
            )
    return events


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def event_study(events: list[dict[str, float]]) -> tuple[list[int], list[float], list[float], list[float]]:
    x_values = list(range(-WINDOW_BEFORE, WINDOW_AFTER + 1))
    paths = [event["path"] for event in events]
    averages = [mean([path[i] for path in paths]) for i in range(len(x_values))]
    lows = [percentile([path[i] for path in paths], 0.25) for i in range(len(x_values))]
    highs = [percentile([path[i] for path in paths], 0.75) for i in range(len(x_values))]
    return x_values, averages, lows, highs


def product_stats(events: list[dict[str, float]]) -> list[dict[str, float]]:
    stats = []
    for product in JUMP_REVERSAL_PARAMS:
        product_events = [event for event in events if event["product"] == product]
        reversed_count = sum(event["reversed_next"] for event in product_events)
        rate = reversed_count / len(product_events) if product_events else 0
        stats.append(
            {
                "product": product,
                "events": len(product_events),
                "reversed_count": reversed_count,
                "rate": rate,
            }
        )
    return stats


def select_example(events: list[dict[str, float]], by_product: dict[str, list[dict[str, float]]]) -> dict[str, float]:
    candidates = [
        event
        for event in events
        if event["product"] == "MICROCHIP_OVAL" and event["reversed_next"] and event["delta"] > 0
    ]
    if not candidates:
        candidates = [event for event in events if event["reversed_next"]]

    return max(candidates, key=lambda event: abs(event["delta"]) + abs(event["next_delta"]))


def add_example_panel(ax, example: dict[str, float], by_product: dict[str, list[dict[str, float]]]) -> None:
    product = example["product"]
    params = JUMP_REVERSAL_PARAMS[product]
    series = by_product[product]
    index = int(example["index"])
    window = series[index - WINDOW_BEFORE : index + WINDOW_AFTER + 1]
    offsets = list(range(-WINDOW_BEFORE, WINDOW_AFTER + 1))
    prices = [point["price"] for point in window]
    event_price = series[index]["price"]
    previous_price = series[index - 1]["price"]
    delta = event_price - previous_price
    fair = event_price + params["beta"] * delta

    action = "SELL" if delta > 0 else "BUY"
    target_position = -params["target"] if delta > 0 else params["target"]
    threshold = params["threshold"]

    ax.plot(offsets, prices, color="#1f77b4", marker="o", linewidth=2.0, markersize=4)
    ax.axvline(0, color="#d62728", linestyle="--", linewidth=1.2)
    ax.axhline(event_price, color="#d62728", linestyle=":", linewidth=1.0)
    ax.axhline(fair, color="#2ca02c", linestyle="--", linewidth=1.2)
    ax.annotate(
        f"{delta:+.0f} jump >= {threshold}\nstrategy: {action} toward {target_position:+d}",
        xy=(0, event_price),
        xytext=(0.56, 0.90),
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "color": "#d62728", "lw": 1.2},
        fontsize=9,
        color="#111111",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#dddddd", "alpha": 0.9},
    )
    ax.annotate(
        f"reversal fair = price + beta x jump\n{fair:.0f} = {event_price:.0f} + {params['beta']} x {delta:.0f}",
        xy=(3, fair),
        xytext=(0.08, 0.30),
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "color": "#2ca02c", "lw": 1.2},
        fontsize=9,
        color="#111111",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#dddddd", "alpha": 0.9},
    )
    ax.set_title(f"Concrete tape example: {product}, day {int(example['day'])}")
    ax.set_xlabel("Trade prints from signal")
    ax.set_ylabel("Trade price")
    ax.grid(True, alpha=0.25)


def plot(events: list[dict[str, float]], by_product: dict[str, list[dict[str, float]]], output_path: Path) -> None:
    stats = product_stats(events)
    x_values, averages, lows, highs = event_study(events)
    reversal_events = [event for event in events if event["reversed_next"]]
    _, reversal_averages, reversal_lows, reversal_highs = event_study(reversal_events)

    fig = plt.figure(figsize=(13, 9))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], width_ratios=[1.2, 1], hspace=0.35, wspace=0.25)
    ax_event = fig.add_subplot(grid[0, :])
    ax_stats = fig.add_subplot(grid[1, 0])
    ax_example = fig.add_subplot(grid[1, 1])

    ax_event.fill_between(
        x_values,
        reversal_lows,
        reversal_highs,
        color="#1f77b4",
        alpha=0.14,
        label="Middle 50% of immediate reversals",
    )
    ax_event.plot(
        x_values,
        averages,
        color="#777777",
        linewidth=2.0,
        linestyle="--",
        label=f"Average of all {len(events)} signals",
    )
    ax_event.plot(
        x_values,
        reversal_averages,
        color="#1f77b4",
        linewidth=2.6,
        label=f"Average when next print reversed ({len(reversal_events)} signals)",
    )
    ax_event.axvline(0, color="#d62728", linestyle="--", linewidth=1.2, label="Jump detected")
    ax_event.axhline(0, color="#333333", linewidth=0.8)
    ax_event.annotate(
        "Before the signal, price has just moved in the jump direction",
        xy=(-1, reversal_averages[x_values.index(-1)]),
        xytext=(-5, min(reversal_averages) * 0.72),
        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.0},
        fontsize=9,
    )
    ax_event.annotate(
        "After entry, negative values mean the tape moved back against the jump",
        xy=(2, reversal_averages[x_values.index(2)]),
        xytext=(1.1, max(reversal_averages) * 0.58),
        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.0},
        fontsize=9,
    )
    ax_event.set_title("Round 5 jump-reversal event study")
    ax_event.set_xlabel("Trade prints from signal")
    ax_event.set_ylabel("Price change in jump direction\n(signal price = 0)")
    ax_event.grid(True, alpha=0.25)
    ax_event.legend(loc="lower right")

    labels = [stat["product"].replace("_", "\n") for stat in stats]
    rates = [stat["rate"] * 100 for stat in stats]
    counts = [stat["events"] for stat in stats]
    bars = ax_stats.bar(range(len(stats)), rates, color="#2ca02c", alpha=0.82)
    ax_stats.axhline(50, color="#555555", linestyle="--", linewidth=1.0)
    ax_stats.set_xticks(range(len(stats)))
    ax_stats.set_xticklabels(labels, rotation=0, fontsize=8)
    ax_stats.set_ylim(0, max(65, max(rates) + 8))
    ax_stats.set_ylabel("Next-print reversal rate (%)")
    ax_stats.set_title("Immediate reversals by product")
    ax_stats.grid(True, axis="y", alpha=0.25)
    for bar, count, rate in zip(bars, counts, rates):
        ax_stats.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{rate:.0f}%\nn={count}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    example = select_example(events, by_product)
    add_example_panel(ax_example, example, by_product)

    fig.suptitle(
        "Jump-reversal trades: detect a large one-print move, then trade for partial snap-back",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.02,
        "Source: data/Round-5/trades_round_5_day_2.csv through day_4.csv. "
        "Trade prints at the same timestamp are volume-weighted before jump detection.",
        ha="center",
        fontsize=9,
        color="#444444",
    )
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    root = find_repo_root(Path.cwd().resolve())
    output_dir = root / "assets" / "historical_prices" / "Round-5"
    output_dir.mkdir(parents=True, exist_ok=True)
    by_product = load_round_5_trade_prices(root)
    events = detect_events(by_product)
    if not events:
        raise RuntimeError("No jump-reversal events found")

    output_path = output_dir / "JUMP_REVERSAL_TRADES.png"
    plot(events, by_product, output_path)
    print(f"saved {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
