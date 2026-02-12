from .indicators import IndicatorSet


class EntrySignal:

    def __init__(self, triggered=False, buy_line=None, expected_return=None, reasons=None):
        self.triggered = triggered
        self.buy_line = buy_line
        self.expected_return_pct = expected_return
        self.reasons = reasons or []


def _closest_resistance_above(price, resistances):
    above = [r for r in resistances if r > price]
    return min(above) if above else None


def check_entry_signal(df, indicators, supports, resistances, config):
    reasons = []

    if len(df) < 3:
        return EntrySignal()

    close = df["close"].iloc[-1]
    low = df["low"].iloc[-1]
    rsi = indicators.rsi
    ema_short = indicators.ema_short
    hist = indicators.macd_hist

    oversold_lvl = config["indicators"]["rsi_oversold"]
    prev_rsi = rsi.iloc[-2]
    curr_rsi = rsi.iloc[-1]
    rsi_ok = (prev_rsi < oversold_lvl) and (curr_rsi > prev_rsi)
    if rsi_ok:
        reasons.append("RSI rising from oversold")

    buf = config["entry_rules"]["support_touch_buffer_pct"]
    support_ok = False
    touched_level = None
    for s in supports:
        if low <= s * (1 + buf) and close > s:
            support_ok = True
            touched_level = s
            break
    if support_ok:
        reasons.append(f"Support rebound near {touched_level:.6f}")

    ema_ok = close > ema_short.iloc[-1]
    if ema_ok:
        reasons.append("Close above short EMA")

    macd_ok = (hist.iloc[-2] < 0) and (hist.iloc[-1] > 0)
    if macd_ok:
        reasons.append("MACD histogram turned positive")

    if not (rsi_ok and support_ok and ema_ok and macd_ok):
        return EntrySignal(reasons=reasons)

    buy_line = close

    nearest_res = _closest_resistance_above(buy_line, resistances)
    exp_ret = None
    if nearest_res:
        exp_ret = ((nearest_res - buy_line) / buy_line) * 100

    min_ret = config["entry_rules"]["min_expected_return_pct"]
    if exp_ret is None or exp_ret < min_ret:
        reasons.append("Expected return too low")
        return EntrySignal(buy_line=buy_line, expected_return=exp_ret, reasons=reasons)

    return EntrySignal(
        triggered=True,
        buy_line=buy_line,
        expected_return=exp_ret,
        reasons=reasons,
    )
