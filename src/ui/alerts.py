import csv
import os
import sys
import time
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

_win_toast = None
if sys.platform == "win32":
    try:
        from win11toast import toast as _win_toast
    except ImportError:
        pass

_media_player = None
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtCore import QUrl
    _media_player = QMediaPlayer()
except Exception:
    pass

SOUND_MODES = ("off", "beep", "alert1", "alert2", "alert3")


class AlertPayload:

    def __init__(self, symbol, price, buy_line, expected_return_pct, reasons):
        self.symbol = symbol
        self.price = price
        self.buy_line = buy_line
        self.expected_return_pct = expected_return_pct
        self.reasons = reasons


class AlertManager:

    def __init__(self, log_csv, log_txt=None, repeat_seconds=30, sound_mode="beep", sounds_dir=None):
        self.log_csv = log_csv
        self.log_txt = log_txt
        self.repeat_seconds = repeat_seconds
        self.sound_mode = sound_mode if sound_mode in SOUND_MODES else "beep"
        self.sounds_dir = Path(sounds_dir) if sounds_dir else Path(__file__).resolve().parent.parent.parent / "sounds"
        self._last_ts = None

    def set_repeat_seconds(self, seconds):
        self.repeat_seconds = max(1, int(seconds))

    def set_sound_mode(self, mode):
        if mode in SOUND_MODES:
            self.sound_mode = mode

    def _play_sound(self):
        if self.sound_mode == "off":
            return
        if self.sound_mode == "beep":
            QApplication.beep()
            return
        if self.sound_mode in ("alert1", "alert2", "alert3"):
            path = self.sounds_dir / f"{self.sound_mode}.mp3"
            if path.exists() and _media_player is not None:
                try:
                    _media_player.setMedia(QMediaContent(QUrl.fromLocalFile(str(path.resolve()))))
                    _media_player.play()
                except Exception:
                    QApplication.beep()
            elif path.exists():
                QApplication.beep()
            return

    def _cooldown_ok(self):
        if self._last_ts is None:
            return True
        return (time.time() - self._last_ts) >= self.repeat_seconds

    def fire(self, payload):
        if not self._cooldown_ok():
            return
        self._last_ts = time.time()

        self._play_sound()

        msg = (
            "ENTRY SIGNAL DETECTED\n"
            f"Price: {payload.price:.6f}\n"
            f"Buy line: {payload.buy_line:.6f}\n"
            f"Expected return: {payload.expected_return_pct:.2f}%\n"
            f"Reason: {', '.join(payload.reasons)}"
        )
        QMessageBox.information(None, "Entry Signal", msg)

        if _win_toast is not None:
            try:
                body = (f"{payload.symbol} @ {payload.price:.4f}  "
                        f"Expected return: {payload.expected_return_pct:.2f}%")
                _win_toast("Entry Signal", body)
            except Exception:
                pass

        self._write_log(payload)

    def _write_log(self, p):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        reasons_str = "; ".join(p.reasons)

        if self.log_csv:
            try:
                with open(self.log_csv, "a", newline="") as f:
                    csv.writer(f).writerow([
                        ts, p.symbol, f"{p.price:.6f}",
                        f"{p.buy_line:.6f}", f"{p.expected_return_pct:.2f}",
                        reasons_str,
                    ])
            except OSError:
                pass

        if self.log_txt:
            try:
                with open(self.log_txt, "a") as f:
                    f.write(
                        f"[{ts}] {p.symbol}  price={p.price:.6f}  "
                        f"buy_line={p.buy_line:.6f}  "
                        f"exp_return={p.expected_return_pct:.2f}%  "
                        f"reasons: {reasons_str}\n"
                    )
            except OSError:
                pass
