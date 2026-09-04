# BIST 100 SMA200 + Volume Screener

Scans a list of BIST symbols and keeps the ones that pass **both** filters:

1. **Trend:** last close is above the 200-day simple moving average (SMA200)
2. **Volume spike:** the last 5-day average volume is more than 1.5x the
   2-year average volume

Passing symbols are printed as a table and drawn into a single chart
(`charts/screen_result.png`): price + SMA200 on top, volume bars with the
period-average line below.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If activation is blocked, run once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python bist_screener.py
```

## Files

| File | Purpose |
|------|---------|
| `bist_screener.py` | The screener. Settings (SMA period, volume multiplier, data range) are constants near the top. |
| `symbols.txt` | The symbol list. One per line, no `.IS` suffix needed. Edit this, not the code. |
| `charts/` | Generated PNG output. |
| `requirements.txt` | Python dependencies. |

## Notes

- Data comes from Yahoo Finance, so an internet connection is required.
- BIST 100 membership changes quarterly. Refresh `symbols.txt` from KAP or
  Borsa Istanbul when needed. A wrong or delisted symbol is skipped, not fatal.
- On a day when nothing passes the filters, no chart is produced. That is expected.
