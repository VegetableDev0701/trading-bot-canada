import numpy as np
import pandas as pd


class IndicatorSet:

    def __init__(self, ema_short, ema_long, sma, rsi, macd, macd_signal,
                 macd_hist, bb_upper, bb_mid, bb_lower, atr):
        """Hold computed indicator series for one OHLCV frame."""
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.sma = sma
        self.rsi = rsi
        self.macd = macd
        self.macd_signal = macd_signal
        self.macd_hist = macd_hist
        self.bb_upper = bb_upper
        self.bb_mid = bb_mid
        self.bb_lower = bb_lower
        self.atr = atr


def ema_series(series, period):
    """Exponential moving average of series over period."""
    return series.ewm(span=period, adjust=False).mean()


def sma_series(series, period):
    """Simple moving average of series over period."""
    return series.rolling(period).mean()


def rsi_series(series, period):
    """Relative strength index (0–100) over period."""
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd_series(series, fast, slow, signal):
    """MACD line, signal line, and histogram (macd - signal)."""
    fast_line = ema_series(series, fast)
    slow_line = ema_series(series, slow)
    macd_line = fast_line - slow_line
    sig = ema_series(macd_line, signal)
    hist = macd_line - sig
    return macd_line, sig, hist


def bollinger_bands(series, period, num_std):
    """Upper, middle, and lower Bollinger bands."""
    mid = sma_series(series, period)
    std = series.rolling(period).std()
    return mid + num_std * std, mid, mid - num_std * std


def atr_series(df, period):
    """Average true range over period from OHLC dataframe."""
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def build_indicator_set(df, cfg):
    """Compute all indicators from config and return an IndicatorSet."""
    c = df["close"]

    ema_s = ema_series(c, cfg["ema_short"])
    ema_l = ema_series(c, cfg["ema_long"])
    sma_val = sma_series(c, cfg["sma_period"])
    rsi_val = rsi_series(c, cfg["rsi_period"])
    macd_val, macd_sig, macd_h = macd_series(
        c, cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])
    bb_up, bb_m, bb_lo = bollinger_bands(c, cfg["bb_period"], cfg["bb_stddev"])
    atr_val = atr_series(df, cfg["atr_period"])

    return IndicatorSet(
        ema_short=ema_s, ema_long=ema_l, sma=sma_val,
        rsi=rsi_val, macd=macd_val, macd_signal=macd_sig,
        macd_hist=macd_h, bb_upper=bb_up, bb_mid=bb_m,
        bb_lower=bb_lo, atr=atr_val,
    )


def _pivot_highs_lows(df, left, right):
    """Find pivot highs and lows using left/right window bars."""
    highs = df["high"].values
    lows = df["low"].values
    p_highs, p_lows = [], []

    for i in range(left, len(df) - right):
        window_h = highs[i - left: i + right + 1]
        window_l = lows[i - left: i + right + 1]
        if highs[i] == window_h.max():
            p_highs.append(float(highs[i]))
        if lows[i] == window_l.min():
            p_lows.append(float(lows[i]))

    return p_highs, p_lows


def _swing_highs_lows(df, lookback):
    """Return last lookback highs and lows as two lists."""
    tail = df.tail(lookback)
    return tail["high"].tolist(), tail["low"].tolist()


def _cluster_levels(levels, tol_pct):
    """Group levels within tol_pct and return cluster means."""
    if not levels:
        return []

    levels = sorted(levels)
    groups = [[levels[0]]]
    for val in levels[1:]:
        if abs(val - groups[-1][-1]) / groups[-1][-1] <= tol_pct:
            groups[-1].append(val)
        else:
            groups.append([val])

    return [float(np.mean(g)) for g in groups]


def build_support_resistance(df, cfg):
    """Compute support and resistance level lists from pivots and swings."""
    p_highs, p_lows = _pivot_highs_lows(df, cfg["pivot_left"], cfg["pivot_right"])
    sw_highs, sw_lows = _swing_highs_lows(df, cfg["swing_lookback"])

    resistances = _cluster_levels(p_highs + sw_highs, cfg["cluster_tolerance_pct"])
    supports = _cluster_levels(p_lows + sw_lows, cfg["cluster_tolerance_pct"])
    return supports, resistances


def classic_pivot_levels(high, low, close):
    """Classic pivot points from prior period H, L, C. Returns dict with PP, R1, R2, S1, S2."""
    pp = (high + low + close) / 3.0
    r1 = 2 * pp - low
    r2 = pp + (high - low)
    s1 = 2 * pp - high
    s2 = pp - (high - low)
    return {"PP": pp, "R1": r1, "R2": r2, "S1": s1, "S2": s2}


def prior_hlc_for_pivots(df, cfg):
    """
    Get (high, low, close) for the prior period used for classic pivot points.
    cfg: pivot_points config with "source" ("bar" | "daily") and "bar_lookback" (int).
    For "bar": uses the last bar_lookback *closed* bars (excludes current open candle).
    For "daily": returns None (caller must use daily df).
    """
    src = (cfg.get("pivot_points") or {}).get("source", "bar")
    lookback = int((cfg.get("pivot_points") or {}).get("bar_lookback", 1))
    if src == "bar":
        # Need at least lookback + 1 rows: lookback closed bars + 1 current (open) candle to skip
        if df.empty or len(df) < lookback + 1:
            return None
        # Exclude last row (current open candle); use only previous closed bar(s)
        closed = df.iloc[-1 - lookback : -1]
        high = float(closed["high"].max())
        low = float(closed["low"].min())
        close = float(closed["close"].iloc[-1])
        return high, low, close
    return None
