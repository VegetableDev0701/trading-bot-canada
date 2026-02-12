import numpy as np
import pandas as pd


class IndicatorSet:

    def __init__(self, ema_short, ema_long, sma, rsi, macd, macd_signal,
                 macd_hist, bb_upper, bb_mid, bb_lower, atr):
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


def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calc_sma(series, period):
    return series.rolling(period).mean()


def calc_rsi(series, period):
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(series, fast, slow, signal):
    fast_line = calc_ema(series, fast)
    slow_line = calc_ema(series, slow)
    macd_line = fast_line - slow_line
    sig = calc_ema(macd_line, signal)
    hist = macd_line - sig
    return macd_line, sig, hist


def calc_bollinger(series, period, num_std):
    mid = calc_sma(series, period)
    std = series.rolling(period).std()
    return mid + num_std * std, mid, mid - num_std * std


def calc_atr(df, period):
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_indicators(df, cfg):
    c = df["close"]

    ema_s = calc_ema(c, cfg["ema_short"])
    ema_l = calc_ema(c, cfg["ema_long"])
    sma_val = calc_sma(c, cfg["sma_period"])
    rsi_val = calc_rsi(c, cfg["rsi_period"])
    macd_val, macd_sig, macd_h = calc_macd(
        c, cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])
    bb_up, bb_m, bb_lo = calc_bollinger(c, cfg["bb_period"], cfg["bb_stddev"])
    atr_val = calc_atr(df, cfg["atr_period"])

    return IndicatorSet(
        ema_short=ema_s, ema_long=ema_l, sma=sma_val,
        rsi=rsi_val, macd=macd_val, macd_signal=macd_sig,
        macd_hist=macd_h, bb_upper=bb_up, bb_mid=bb_m,
        bb_lower=bb_lo, atr=atr_val,
    )


def _find_pivots(df, left, right):
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


def _get_recent_swings(df, lookback):
    tail = df.tail(lookback)
    return tail["high"].tolist(), tail["low"].tolist()


def _cluster(levels, tol_pct):
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


def compute_support_resistance(df, cfg):
    p_highs, p_lows = _find_pivots(df, cfg["pivot_left"], cfg["pivot_right"])
    sw_highs, sw_lows = _get_recent_swings(df, cfg["swing_lookback"])

    resistances = _cluster(p_highs + sw_highs, cfg["cluster_tolerance_pct"])
    supports = _cluster(p_lows + sw_lows, cfg["cluster_tolerance_pct"])
    return supports, resistances
