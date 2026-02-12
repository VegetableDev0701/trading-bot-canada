"""
Test cases for entry signal logic.
Run: python -m pytest tests/test_entry_logic.py -v
"""
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.logic.indicators import IndicatorSet
from src.logic.logic import check_entry_signal


def _config():
    return {
        "indicators": {"rsi_oversold": 30},
        "entry_rules": {"support_touch_buffer_pct": 0.002, "min_expected_return_pct": 1.0},
    }


def test_signal_not_triggered_too_few_rows():
    df = pd.DataFrame({"close": [100.0, 101.0], "low": [99.0, 100.0]})
    ind = IndicatorSet(
        ema_short=pd.Series([100, 101]),
        ema_long=pd.Series([100, 101]),
        sma=pd.Series([100, 101]),
        rsi=pd.Series([25, 32]),
        macd=pd.Series([0.0, 0.0]),
        macd_signal=pd.Series([0.0, 0.0]),
        macd_hist=pd.Series([-0.1, 0.1]),
        bb_upper=pd.Series([102, 103]),
        bb_mid=pd.Series([100, 101]),
        bb_lower=pd.Series([98, 99]),
        atr=pd.Series([1.0, 1.0]),
    )
    sig = check_entry_signal(df, ind, [99.0], [103.0], _config())
    assert sig.triggered is False
    assert len(df) < 3


def test_signal_triggered_all_conditions_met():
    df = pd.DataFrame({
        "close": [100.0, 99.0, 101.0],
        "low": [98.0, 97.0, 99.15],
    })
    ind = IndicatorSet(
        ema_short=pd.Series([100.0, 99.5, 100.0]),
        ema_long=pd.Series([100.0, 99.5, 99.8]),
        sma=pd.Series([100.0, 99.5, 100.0]),
        rsi=pd.Series([35.0, 25.0, 32.0]),
        macd=pd.Series([0.0, 0.0, 0.0]),
        macd_signal=pd.Series([0.0, 0.0, 0.0]),
        macd_hist=pd.Series([0.0, -0.1, 0.1]),
        bb_upper=pd.Series([102.0, 101.0, 103.0]),
        bb_mid=pd.Series([100.0, 99.0, 101.0]),
        bb_lower=pd.Series([98.0, 97.0, 99.0]),
        atr=pd.Series([1.0, 1.0, 1.0]),
    )
    supports = [99.1]
    resistances = [103.0]
    cfg = _config()
    sig = check_entry_signal(df, ind, supports, resistances, cfg)
    assert sig.triggered is True
    assert sig.buy_line == 101.0
    assert sig.expected_return_pct is not None
    assert sig.expected_return_pct >= 1.0


def test_signal_not_triggered_expected_return_too_low():
    df = pd.DataFrame({
        "close": [100.0, 99.0, 101.0],
        "low": [98.0, 97.0, 99.15],
    })
    ind = IndicatorSet(
        ema_short=pd.Series([100.0, 99.5, 100.0]),
        ema_long=pd.Series([100.0, 99.5, 99.8]),
        sma=pd.Series([100.0, 99.5, 100.0]),
        rsi=pd.Series([35.0, 25.0, 32.0]),
        macd=pd.Series([0.0, 0.0, 0.0]),
        macd_signal=pd.Series([0.0, 0.0, 0.0]),
        macd_hist=pd.Series([0.0, -0.1, 0.1]),
        bb_upper=pd.Series([102.0, 101.0, 103.0]),
        bb_mid=pd.Series([100.0, 99.0, 101.0]),
        bb_lower=pd.Series([98.0, 97.0, 99.0]),
        atr=pd.Series([1.0, 1.0, 1.0]),
    )
    supports = [99.1]
    resistances = [101.2]
    cfg = _config()
    sig = check_entry_signal(df, ind, supports, resistances, cfg)
    assert sig.triggered is False
    assert "Expected return too low" in sig.reasons


if __name__ == "__main__":
    test_signal_not_triggered_too_few_rows()
    test_signal_triggered_all_conditions_met()
    test_signal_not_triggered_expected_return_too_low()
    print("All tests passed.")
