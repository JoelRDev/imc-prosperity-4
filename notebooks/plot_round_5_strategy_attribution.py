from __future__ import annotations

import csv
import os
import re
import subprocess
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/imc-prosperity-matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter


RUN_CALL_BLOCK = """        self.trade_pebbles(result, state)
        self.trade_jump_reversal(result, state, prev_mids)
        self.trade_pair_relative_value(result, state, cache, current_mids)
        self.trade_pebbles_passive(result, state, current_mids)
        self.trade_snackpack_basket(result, state, cache, current_mids)
        self.trade_bucket_ema_baskets(result, state, cache, current_mids)
        self.trade_snackpack_market_making(result, state, current_mids, ema_stats)
        self.trade_slow_mean_reversion(result, state, current_mids, ema_stats)
        self.trade_secondary_passive_market_making(result, state, current_mids)
"""

COMPONENTS = [
    {
        "label": "Full strategy",
        "filename": "full_strategy.py",
        "calls": [
            "        self.trade_pebbles(result, state)",
            "        self.trade_jump_reversal(result, state, prev_mids)",
            "        self.trade_pair_relative_value(result, state, cache, current_mids)",
            "        self.trade_pebbles_passive(result, state, current_mids)",
            "        self.trade_snackpack_basket(result, state, cache, current_mids)",
            "        self.trade_bucket_ema_baskets(result, state, cache, current_mids)",
            "        self.trade_snackpack_market_making(result, state, current_mids, ema_stats)",
            "        self.trade_slow_mean_reversion(result, state, current_mids, ema_stats)",
            "        self.trade_secondary_passive_market_making(result, state, current_mids)",
        ],
        "reference": True,
    },
    {
        "label": "PEBBLES hard arb",
        "filename": "pebbles_hard_arb.py",
        "calls": ["        self.trade_pebbles(result, state)"],
    },
    {
        "label": "Jump reversal",
        "filename": "jump_reversal.py",
        "calls": ["        self.trade_jump_reversal(result, state, prev_mids)"],
    },
    {
        "label": "Pair relative value",
        "filename": "pair_relative_value.py",
        "calls": ["        self.trade_pair_relative_value(result, state, cache, current_mids)"],
    },
    {
        "label": "PEBBLES passive",
        "filename": "pebbles_passive.py",
        "calls": ["        self.trade_pebbles_passive(result, state, current_mids)"],
    },
    {
        "label": "SNACKPACK basket",
        "filename": "snackpack_basket.py",
        "calls": ["        self.trade_snackpack_basket(result, state, cache, current_mids)"],
    },
    {
        "label": "Bucket basket EMA",
        "filename": "bucket_basket_ema.py",
        "calls": ["        self.trade_bucket_ema_baskets(result, state, cache, current_mids)"],
    },
    {
        "label": "SNACKPACK passive MM",
        "filename": "snackpack_passive_mm.py",
        "calls": ["        self.trade_snackpack_market_making(result, state, current_mids, ema_stats)"],
    },
    {
        "label": "Slow single-name MR",
        "filename": "slow_single_name_mr.py",
        "calls": ["        self.trade_slow_mean_reversion(result, state, current_mids, ema_stats)"],
    },
    {
        "label": "Secondary passive MM",
        "filename": "secondary_passive_mm.py",
        "calls": ["        self.trade_secondary_passive_market_making(result, state, current_mids)"],
    },
]

DAYS = [2, 3, 4]


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "strategies" / "round-5.py").is_file() and (candidate / "assets").is_dir():
            return candidate
    raise FileNotFoundError("Could not find repo root")


def make_component_strategy(source: str, calls: list[str]) -> str:
    replacement = "\n".join(calls) + "\n"
    if RUN_CALL_BLOCK not in source:
        raise ValueError("Could not find the Round 5 run-call block to replace")
    return source.replace(RUN_CALL_BLOCK, replacement)


def parse_backtester_output(output: str) -> dict[int, int]:
    summary = output.split("Profit summary:")[-1]
    day_pnl = {}
    for match in re.finditer(r"Round 5 day ([234]):\s+(-?[\d,]+)", summary):
        day = int(match.group(1))
        pnl = int(match.group(2).replace(",", ""))
        day_pnl[day] = pnl

    missing_days = [day for day in DAYS if day not in day_pnl]
    if missing_days:
        raise ValueError(f"Could not parse PnL for days {missing_days}")

    return day_pnl


def run_backtest(root: Path, strategy_path: Path) -> dict[int, int]:
    executable = root / ".venv" / "bin" / "prosperity4btest"
    command = [
        str(executable if executable.exists() else "prosperity4btest"),
        "cli",
        str(strategy_path),
        "5",
        "--merge-pnl",
        "--no-out",
        "--no-progress",
    ]
    result = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Backtest failed for {strategy_path.name}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return parse_backtester_output(result.stdout)


def run_component_backtests(root: Path) -> list[dict[str, object]]:
    source = (root / "strategies" / "round-5.py").read_text()
    rows = []
    with tempfile.TemporaryDirectory(prefix="round5_component_") as temp_dir:
        temp_path = Path(temp_dir)
        for component in COMPONENTS:
            strategy_path = temp_path / str(component["filename"])
            strategy_path.write_text(make_component_strategy(source, component["calls"]))
            day_pnl = run_backtest(root, strategy_path)
            rows.append(
                {
                    "label": component["label"],
                    "reference": bool(component.get("reference", False)),
                    "day_pnl": day_pnl,
                    "total": sum(day_pnl.values()),
                }
            )
            print(f"{component['label']}: {sum(day_pnl.values()):,}")
    return rows


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["strategy_component", "day_2", "day_3", "day_4", "total"])
        for row in rows:
            day_pnl = row["day_pnl"]
            writer.writerow([row["label"], day_pnl[2], day_pnl[3], day_pnl[4], row["total"]])


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{abs(value) / 1000:.0f}k"


def plot(rows: list[dict[str, object]], output_path: Path) -> None:
    full = next(row for row in rows if row["reference"])
    components = [row for row in rows if not row["reference"]]
    components.sort(key=lambda row: row["total"], reverse=True)

    labels = [row["label"] for row in components]
    totals = [row["total"] for row in components]
    day_matrix = [[row["day_pnl"][day] for day in DAYS] for row in components]

    fig = plt.figure(figsize=(13, 9))
    grid = fig.add_gridspec(2, 1, height_ratios=[1.25, 1], hspace=0.34)
    ax_total = fig.add_subplot(grid[0])
    ax_heatmap = fig.add_subplot(grid[1])

    y_positions = list(range(len(labels)))
    colors = ["#2ca02c" if value >= 0 else "#d62728" for value in totals]
    x_limit = max(max(totals), full["total"]) * 1.16
    ax_total.barh(y_positions, totals, color=colors, alpha=0.85)
    ax_total.axvline(0, color="#333333", linewidth=0.8)
    ax_total.axvline(full["total"], color="#111111", linestyle="--", linewidth=1.2)
    ax_total.text(
        full["total"] + x_limit * 0.01,
        -0.68,
        f"full strategy: {full['total']:,}",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#111111",
    )
    ax_total.set_yticks(y_positions)
    ax_total.set_yticklabels(labels)
    ax_total.invert_yaxis()
    ax_total.set_title("Standalone Round 5 PnL by strategy module")
    ax_total.set_xlabel("Backtested PnL across days 2-4")
    ax_total.set_xlim(0, x_limit)
    ax_total.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: money(value)))
    ax_total.grid(True, axis="x", alpha=0.25)
    for y, value in zip(y_positions, totals):
        x_offset = max(abs(max(totals)), abs(min(totals)), 1) * 0.012
        ha = "left" if value >= 0 else "right"
        ax_total.text(value + (x_offset if value >= 0 else -x_offset), y, f"{value:,}", va="center", ha=ha, fontsize=9)

    max_abs = max(abs(value) for row in day_matrix for value in row)
    cmap = LinearSegmentedColormap.from_list("pnl", ["#d62728", "#f7f7f7", "#2ca02c"])
    norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0, vmax=max_abs)
    image = ax_heatmap.imshow(day_matrix, cmap=cmap, norm=norm, aspect="auto")
    ax_heatmap.set_xticks(range(len(DAYS)))
    ax_heatmap.set_xticklabels([f"day {day}" for day in DAYS])
    ax_heatmap.set_yticks(range(len(labels)))
    ax_heatmap.set_yticklabels(labels)
    ax_heatmap.set_title("Day-by-day module-only PnL")
    for row_index, row_values in enumerate(day_matrix):
        for col_index, value in enumerate(row_values):
            text_color = "white" if abs(value) > max_abs * 0.58 else "#111111"
            ax_heatmap.text(col_index, row_index, f"{value:,}", ha="center", va="center", fontsize=8, color=text_color)
    colorbar = fig.colorbar(image, ax=ax_heatmap, fraction=0.025, pad=0.02)
    colorbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: money(value)))

    fig.suptitle("Which Round 5 strategy modules made money?", fontsize=16, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.02,
        "Source: prosperity4btest 5.0.0, round 5 days 2-4. Components are backtested alone, "
        "so values are standalone diagnostics and do not add up to the full strategy.",
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

    rows = run_component_backtests(root)
    write_csv(rows, output_dir / "STRATEGY_COMPONENT_PNL.csv")
    plot(rows, output_dir / "STRATEGY_COMPONENT_PNL.png")
    print(f"saved {output_dir.relative_to(root) / 'STRATEGY_COMPONENT_PNL.png'}")


if __name__ == "__main__":
    main()
