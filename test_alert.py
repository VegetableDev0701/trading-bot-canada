"""
One-off test for alert popup, sound, Windows toast, and CSV/TXT logging.
  python test_alert.py          -- show popup (click OK), beep, toast, write CSV+TXT
  python test_alert.py --no-gui -- only append to CSV and TXT (no popup), then exit
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _resolve(p):
    return p if os.path.isabs(p) else str(ROOT / p)


def main():
    no_gui = "--no-gui" in sys.argv

    if no_gui:
        from src.ui.alerts import AlertManager, AlertPayload
        log_csv = _resolve("alerts.csv")
        log_txt = _resolve("alerts.txt")
        mgr = AlertManager(log_csv=log_csv, log_txt=log_txt, repeat_seconds=30, sound=False)
        payload = AlertPayload(
            symbol="BTC/USDT",
            price=97500.25,
            buy_line=97400.0,
            expected_return_pct=2.35,
            reasons=["RSI rising from oversold", "Support rebound near 97200.0", "Close above short EMA", "MACD histogram turned positive"],
        )
        mgr._write_log(payload)
        print(f"Appended to {log_csv} and {log_txt}")
        return

    from PyQt5.QtWidgets import QApplication
    from src.ui.alerts import AlertManager, AlertPayload

    app = QApplication(sys.argv)
    log_csv = _resolve("alerts.csv")
    log_txt = _resolve("alerts.txt")
    mgr = AlertManager(log_csv=log_csv, log_txt=log_txt, repeat_seconds=30, sound=True)
    payload = AlertPayload(
        symbol="BTC/USDT",
        price=97500.25,
        buy_line=97400.0,
        expected_return_pct=2.35,
        reasons=["RSI rising from oversold", "Support rebound near 97200.0", "Close above short EMA", "MACD histogram turned positive"],
    )
    print("Firing test alert. You should see: popup, optional beep, optional toast.")
    print(f"Logs: {log_csv} and {log_txt}")
    mgr.fire(payload)
    print("Done. Check the two files for the new row/line.")


if __name__ == "__main__":
    main()
