"""
Generate demo_candles.csv for run_demo.py.
Run once: python demo_data.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "demo_candles.csv"

N = 200
np.random.seed(42)

base = 97000.0
close = base
rows = []
t = pd.Timestamp("2026-02-12 00:00:00", tz="UTC")

for i in range(N):
    ret = np.random.randn() * 0.002
    if i >= 180:
        ret -= 0.001
    if i == 198:
        ret = -0.003
    if i == 199:
        ret = 0.004
    open_ = close
    close = open_ * (1 + ret)
    high = max(open_, close) + abs(np.random.randn()) * 20
    low = min(open_, close) - abs(np.random.randn()) * 20
    vol = 100 + np.random.rand() * 500
    rows.append({
        "timestamp": t,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": vol,
    })
    t += pd.Timedelta(minutes=1)

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print(f"Wrote {OUT} ({len(df)} rows)")
