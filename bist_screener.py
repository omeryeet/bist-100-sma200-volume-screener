"""
BIST 100 screener.

Filters:
  1) Last close > SMA200                                  (long-term uptrend)
  2) Last 5-day average volume > period average * 1.5     (volume spike)

Symbols that pass both filters are printed as a table and plotted
into a single PNG under charts/.
"""

import os
import sys

import yfinance as yf
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SYMBOLS_FILE = "symbols.txt"


def load_symbols():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SYMBOLS_FILE)

    if not os.path.exists(path):
        print(f"[ERROR] {SYMBOLS_FILE} not found. Create it next to this script, "
              f"one symbol per line.")
        sys.exit(1)

    symbols = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if not line.upper().endswith(".IS"):
                line = line.upper() + ".IS"
            symbols.append(line)

    if not symbols:
        print(f"[ERROR] {SYMBOLS_FILE} has no valid symbols.")
        sys.exit(1)

    return symbols


SYMBOLS = load_symbols()


SMA_PERIOD = 200
RECENT_DAYS = 5
VOLUME_MULTIPLIER = 1.5
DATA_PERIOD = "2y"
DATA_INTERVAL = "1d"

CHARTS_DIR = "charts"
CHART_FILE = "screen_result.png"


def screen_symbol(symbol):
    df = yf.download(
        symbol,
        period=DATA_PERIOD,
        interval=DATA_INTERVAL,
        auto_adjust=True,
        progress=False,
    )

    if df.empty or len(df) < SMA_PERIOD:
        print(f"  [SKIPPED] {symbol}: not enough data "
              f"({len(df)} days, need at least {SMA_PERIOD}).")
        return None, None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["SMA200"] = df["Close"].rolling(SMA_PERIOD).mean()

    last_row = df.iloc[-1]
    last_close = last_row["Close"]
    last_sma200 = last_row["SMA200"]

    recent_avg_volume = df["Volume"].tail(RECENT_DAYS).mean()
    period_avg_volume = df["Volume"].mean()

    if period_avg_volume > 0:
        volume_ratio = recent_avg_volume / period_avg_volume
    else:
        volume_ratio = 0

    volume_change_pct = (volume_ratio - 1) * 100

    trend_ok = last_close > last_sma200
    volume_ok = recent_avg_volume > (period_avg_volume * VOLUME_MULTIPLIER)

    if trend_ok and volume_ok:
        result = {
            "Symbol": symbol,
            "Last Close": round(last_close, 2),
            "SMA200": round(last_sma200, 2),
            "Volume Change %": round(volume_change_pct, 1),
        }
        return result, df

    return None, None


def plot_results(chart_data):
    if not chart_data:
        return None

    n = len(chart_data)
    fig, axes = plt.subplots(
        2 * n, 1,
        figsize=(12, 4 * n),
        gridspec_kw={"height_ratios": [3, 1] * n},
    )

    if n == 1:
        axes = list(axes)

    for i, (symbol, df) in enumerate(chart_data):
        price_ax = axes[2 * i]
        volume_ax = axes[2 * i + 1]

        last_close = df["Close"].iloc[-1]
        last_sma200 = df["SMA200"].iloc[-1]

        price_ax.plot(df.index, df["Close"], label="Price", color="black")
        price_ax.plot(df.index, df["SMA200"], label="SMA200", color="orange", linestyle="--")
        price_ax.set_title(f"{symbol}   Last: {last_close:.2f}   SMA200: {last_sma200:.2f}")
        price_ax.legend(loc="upper left")
        price_ax.grid(alpha=0.3)

        volume_ax.bar(df.index, df["Volume"], color="steelblue")
        volume_ax.axhline(
            df["Volume"].mean(),
            color="red",
            linestyle="--",
            label="Period avg volume",
        )
        volume_ax.legend(loc="upper left")
        volume_ax.set_ylabel("Volume")

    fig.tight_layout()

    os.makedirs(CHARTS_DIR, exist_ok=True)
    path = os.path.join(CHARTS_DIR, CHART_FILE)
    fig.savefig(path, dpi=100)
    plt.close(fig)

    return path


def main():
    print("BIST 100 screener starting...")
    print(f"Symbols to scan: {len(SYMBOLS)}\n")

    matches = []
    chart_data = []

    for symbol in SYMBOLS:
        print(f"Scanning: {symbol}")

        try:
            result, df = screen_symbol(symbol)

            if result is not None:
                matches.append(result)
                chart_data.append((symbol, df))
                print(f"  [MATCH] {symbol} passes both filters.")

        except Exception as error:
            print(f"  [ERROR] {symbol} failed, skipping. Reason: {error}")
            continue

    print("\n" + "=" * 50)
    print("SCREEN RESULTS")
    print("=" * 50)

    if len(matches) == 0:
        print("No symbols passed the filters.")
        return

    result_df = pd.DataFrame(matches)
    result_df = result_df.sort_values("Volume Change %", ascending=False)
    result_df = result_df.reset_index(drop=True)
    result_df.index = result_df.index + 1

    print(result_df.to_string())
    print(f"\n{len(matches)} symbols passed the filters.")

    path = plot_results(chart_data)
    if path:
        print(f"Chart saved: {path}")


if __name__ == "__main__":
    main()
