"""
Demo: run the bot pipeline on sample data and fire a test alert.
Shows how indicators, support/resistance, and entry logic work.
Run from project root: python run_demo.py

  --no-alert  skip the popup/alert (only print pipeline result and do not write CSV/TXT)
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _resolve(p):
    return p if os.path.isabs(p) else str(ROOT / p)


def main():
    import json
    import pandas as pd

    from src.logic.indicators import compute_indicators, compute_support_resistance
    from src.logic.logic import check_entry_signal

    no_alert = "--no-alert" in sys.argv

    cfg_path = ROOT / "config.json"
    if not cfg_path.exists():
        print("config.json not found. Run from project root.")
        sys.exit(1)
    with cfg_path.open() as f:
        cfg = json.load(f)

    csv_path = ROOT / "demo_candles.csv"
    if not csv_path.exists():
        print("demo_candles.csv not found. Run: python demo_data.py")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df.shape[0] < 50:
        print("Need at least 50 rows in demo_candles.csv")
        sys.exit(1)

    print("=" * 60)
    print("DEMO: Bot pipeline on demo data")
    print("=" * 60)
    print(f"Loaded {len(df)} candles from demo_candles.csv")
    print(f"Last close: {df['close'].iloc[-1]:.2f}")
    print()

    ind = compute_indicators(df, cfg["indicators"])
    supports, resistances = compute_support_resistance(df, cfg["support_resistance"])

    print("Support levels (clustered):", [f"{s:.2f}" for s in supports[:8]])
    print("Resistance levels (clustered):", [f"{r:.2f}" for r in resistances[:8]])
    print()

    sig = check_entry_signal(df, ind, supports, resistances, cfg)

    print("Entry signal result:")
    print("  Triggered:", sig.triggered)
    if sig.buy_line is not None:
        print("  Buy line:", sig.buy_line)
    if sig.expected_return_pct is not None:
        print("  Expected return %:", f"{sig.expected_return_pct:.2f}%")
    print("  Reasons:", sig.reasons)
    print()

    if no_alert:
        print("Skipped alert (--no-alert). Done.")
        return

    print("Firing test alert (popup + sound + toast + CSV/TXT)...")
    from PyQt5.QtWidgets import QApplication
    from src.ui.alerts import AlertManager, AlertPayload

    app = QApplication(sys.argv)
    alerts_cfg = cfg["alerts"]
    sound_mode = alerts_cfg.get("sound_mode", "beep" if alerts_cfg.get("sound", True) else "off")
    mgr = AlertManager(
        log_csv=_resolve(alerts_cfg["log_csv"]),
        log_txt=_resolve(alerts_cfg.get("log_txt", "alerts.txt")),
        repeat_seconds=alerts_cfg.get("repeat_seconds", 30),
        sound_mode=sound_mode,
        sounds_dir=str(ROOT / "sounds"),
    )
    payload = AlertPayload(
        symbol=cfg.get("default_symbol", "BTC/USDT"),
        price=float(df["close"].iloc[-1]),
        buy_line=sig.buy_line if sig.buy_line is not None else float(df["close"].iloc[-1]),
        expected_return_pct=sig.expected_return_pct if sig.expected_return_pct is not None else 0.0,
        reasons=sig.reasons if sig.reasons else ["Demo run"],
    )
    mgr.fire(payload)
    print("Done. Check alerts.csv and alerts.txt.")


if __name__ == "__main__":
    main()
