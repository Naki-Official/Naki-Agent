import json
import talib
import logging
import numpy as np
from typing import List, Optional, Dict, Any

from tools.cryptocompare import CryptoCompareTools

logger = logging.getLogger(__name__)


class TechnicalAnalysis:
    """
    The TechnicalAnalysis class provides methods for performing technical chart analysis on
    crypto coins using TA‑Lib indicators and data from CryptoCompareTools.
    
    It focuses on a mid-term (4-hour) analysis to identify major trend and swing highs/lows,
    and a short-term (1-hour) analysis for immediate signals like RSI and MACD. The results
    include a recommendation, overall score, indicators, swing levels, and a suggested trade.
    """

    def __init__(self, COMPARE_CRYPTO_API_KEY: Optional[str] = None):
        """
        Initialize the TechnicalAnalysis class.

        Args:
            COMPARE_CRYPTO_API_KEY (Optional[str]): API key for CryptoCompare.
        """
        self.cc_tools = CryptoCompareTools(api_key=COMPARE_CRYPTO_API_KEY)

    def comprehensive_ta_analysis(
        self,
        from_symbol: str = "btc",
        to_symbol: str = "usd",
        fourh_limit: int = 200,  # ~200 * 4h = ~800 hours (~33 days)
        hour_limit: int = 100,   # ~100 hours (~4 days) for immediate signals
        lookback_for_swing: int = 50  # # of 4h bars to find local maxima/minima
    ) -> str:
        """
        Perform a mid- to short-term technical analysis:
          (1) 4-hour data for the major trend (SMA50 vs. SMA200) + swing highs/lows
          (2) 1-hour data for RSI and MACD
          (3) Score-based recommendation (LONG, SHORT, NO_ACTION)
          (4) Suggested trade with entry, stop_loss, and take_profit

        Returns:
            str (JSON): Includes:
                - recommendation: str
                - overall_score: int
                - reason: list of messages
                - indicator_values: dict of final indicator readings
                - swing_levels: local highs/lows
                - suggested_trade: dict with entry, stop_loss, take_profit
        """
        try:
            logger.info(
                "Starting mid-term TA analysis for %s/%s using 4h & 1h data (swing highs/lows).",
                from_symbol, to_symbol
            )

            # --- (1) FOUR-HOUR DATA ---
            fourh_data = self._fetch_fourh_data(from_symbol, to_symbol, fourh_limit)
            mid_trend, sma_vals, swing_highs, swing_lows = self._process_fourh_data(
                closes=fourh_data["close"],
                highs=fourh_data["high"],
                lows=fourh_data["low"],
                lookback_for_swing=lookback_for_swing
            )

            # --- (2) ONE-HOUR DATA ---
            hour_data = self._fetch_oneh_data(from_symbol, to_symbol, hour_limit)
            rsi_1h, macd_1h_vals = self._process_oneh_data(hour_data["close"])

            # --- (3) SCORING & RECOMMENDATION ---
            overall_score, reason_list, recommendation = self._build_score_and_recommendation(
                mid_trend=mid_trend,
                rsi_1h=rsi_1h,
                macd_hist=macd_1h_vals["hist"]
            )

            # --- (4) SUGGESTED TRADE ---
            suggested_trade, more_reasons = self._suggest_trade(
                recommendation, swing_highs, swing_lows
            )
            print('=====================SUGGESTED TRADE=====================')
            reason_list.extend(more_reasons)

            # --- (5) BUILD FINAL REPORT ---
            report = self._build_report(
                recommendation,
                overall_score,
                reason_list,
                sma_vals,
                rsi_1h,
                macd_1h_vals,
                swing_highs,
                swing_lows,
                suggested_trade
            )
            return report

        except Exception as e:
            logger.error("Error in mid-term TA analysis (swing highs/lows): %s", e)
            return json.dumps({"error": str(e)})

    # -------------------------------------------------------------------------
    #                           PRIVATE HELPER METHODS
    # -------------------------------------------------------------------------

    def _fetch_fourh_data(
        self,
        from_symbol: str,
        to_symbol: str,
        limit: int
    ) -> Dict[str, Any]:
        """
        Fetch 4-hour OHLCV data from CryptoCompareTools.
        Each candle covers a 4-hour span.
        """
        fourh_json = self.cc_tools.historical_ohlcv_hour(
            from_symbol, to_symbol,
            limit=limit,
            aggregate=4
        )
        return self._parse_ohlcv(fourh_json)

    def _fetch_oneh_data(
        self,
        from_symbol: str,
        to_symbol: str,
        limit: int
    ) -> Dict[str, Any]:
        """
        Fetch 1-hour OHLCV data from CryptoCompareTools.
        """
        ohlcv_data = self.cc_tools.historical_ohlcv_hour(
            from_symbol, to_symbol,
            limit=limit,
            aggregate=1
        )
        return self._parse_ohlcv(ohlcv_data)

    def _parse_ohlcv(self, ohlcv_data: list) -> Dict[str, Any]:
        """
        Parse CryptoCompare OHLCV. Return a dict of NumPy arrays:
        { 'open', 'high', 'low', 'close', 'volume' } (indexed in ascending time).
        """
        # Sort by time ascending
        ohlcv_data = sorted(ohlcv_data, key=lambda x: x["time"])

        return {
            "open":   np.array([d["open"]   for d in ohlcv_data], dtype=float),
            "high":   np.array([d["high"]   for d in ohlcv_data], dtype=float),
            "low":    np.array([d["low"]    for d in ohlcv_data], dtype=float),
            "close":  np.array([d["close"]  for d in ohlcv_data], dtype=float),
            "volume": np.array([d.get("volumeto", 0) for d in ohlcv_data], dtype=float)
        }

    def _process_fourh_data(
        self,
        closes: np.array,
        highs: np.array,
        lows: np.array,
        lookback_for_swing: int
    ) -> (str, Dict[str, float], List[float], List[float]):
        """
        Process 4h data to:
          - Compute SMA50 vs. SMA200 to determine mid-term trend
          - Identify swing highs/lows within the last 'lookback_for_swing' bars
        """
        if len(closes) < 200:
            raise ValueError("Not enough 4-hour data to compute SMA200 for mid-term trend.")

        # SMA
        sma50 = talib.SMA(closes, timeperiod=50)
        sma200 = talib.SMA(closes, timeperiod=200)
        last_sma50 = sma50[-1] if sma50[-1] else 0.0
        last_sma200 = sma200[-1] if sma200[-1] else 0.0
        mid_trend = "bullish" if last_sma50 > last_sma200 else "bearish"

        # Local swing highs/lows
        local_highs, local_lows = self._find_swing_highs_lows(highs, lows, lookback_for_swing)
        return (
            mid_trend,
            {
                "sma50_4h": float(last_sma50),
                "sma200_4h": float(last_sma200),
            },
            local_highs,
            local_lows
        )

    def _find_swing_highs_lows(
        self,
        highs: np.array,
        lows: np.array,
        window: int
    ) -> (List[float], List[float]):
        """
        Return two lists:
          - local_highs (descending)
          - local_lows  (ascending)
        within the last `window` bars (excluding final bar for 'confirmed' swing).
        """
        local_highs = []
        local_lows = []

        start_idx = max(1, len(highs) - window)
        end_idx = len(highs) - 1

        for i in range(start_idx, end_idx):
            # local max
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                local_highs.append(highs[i])
            # local min
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                local_lows.append(lows[i])

        local_highs.sort(reverse=True)
        local_lows.sort()

        return local_highs, local_lows

    def _process_oneh_data(
        self,
        closes: np.array
    ) -> (float, Dict[str, float]):
        """
        Process 1-hour data to compute RSI(14) and MACD(12,26,9).
        Returns:
          - latest RSI value
          - dict of latest { "macd", "signal", "hist" }
        """
        if len(closes) < 26:
            raise ValueError("Not enough 1-hour data to compute MACD(12,26).")

        rsi_vals = talib.RSI(closes, timeperiod=14)
        latest_rsi = float(rsi_vals[-1])

        macd_vals, macd_sig, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
        return (
            latest_rsi,
            {
                "macd":   float(macd_vals[-1]),
                "signal": float(macd_sig[-1]),
                "hist":   float(macd_hist[-1])
            }
        )

    def _build_score_and_recommendation(
        self,
        mid_trend: str,
        rsi_1h: float,
        macd_hist: float
    ) -> (int, List[str], str):
        """
        Build an overall score and produce a recommendation: LONG, SHORT, or NO_ACTION.
        Also returns a list of reasons.
        """
        overall_score = 0
        reason_list = []

        # Mid-term trend (4h)
        if mid_trend == "bullish":
            overall_score += 1
            reason_list.append("4h trend is bullish (SMA50 > SMA200).")
        else:
            overall_score -= 1
            reason_list.append("4h trend is bearish (SMA50 <= SMA200).")

        # RSI (1-hour)
        if rsi_1h < 30:
            overall_score += 1
            reason_list.append(f"RSI(14,1h) oversold at {rsi_1h:.2f}.")
        elif rsi_1h > 70:
            overall_score -= 1
            reason_list.append(f"RSI(14,1h) overbought at {rsi_1h:.2f}.")
        else:
            reason_list.append(f"RSI(14,1h) neutral at {rsi_1h:.2f}.")

        # MACD histogram (1-hour)
        if macd_hist > 0:
            overall_score += 1
            reason_list.append("MACD(1h) histogram positive -> bullish momentum.")
        else:
            overall_score -= 1
            reason_list.append("MACD(1h) histogram negative -> bearish momentum.")

        # Final recommendation
        if overall_score >= 2:
            recommendation = "LONG"
            reason_list.append("Overall score >= 2 -> LONG signal.")
        elif overall_score <= -2:
            recommendation = "SHORT"
            reason_list.append("Overall score <= -2 -> SHORT signal.")
        else:
            recommendation = "NO_ACTION"
            reason_list.append("Score in [-1,1] -> NO_ACTION.")

        return overall_score, reason_list, recommendation

    def _suggest_trade(
        self,
        recommendation: str,
        local_highs: List[float],
        local_lows: List[float]
    ) -> (Dict[str, float], List[str]):
        """
        Suggest entry, stop_loss, and take_profit levels based on swing highs/lows.
        """
        reason_list = []
        trade = {"entry": None, "stop_loss": None, "take_profit": None}

        if not local_highs and not local_lows:
            reason_list.append("No local swing highs/lows found. No trade suggested.")
            return trade, reason_list

        # We pick top 2 resistances (local_highs[0..1]) and top 2 supports (local_lows[0..1]).
        r1 = local_highs[0] if local_highs else None
        r2 = local_highs[1] if len(local_highs) > 1 else None
        s1 = local_lows[0]  if local_lows else None
        s2 = local_lows[1]  if len(local_lows) > 1 else None

        # fallback
        if r1 is None: r1 = 999999
        if r2 is None: r2 = 999999
        if s1 is None: s1 = 0
        if s2 is None: s2 = 0

        if recommendation == "LONG":
            entry = s1
            stop_loss = s2 * 0.98 if s2 else entry * 0.8
            tp = r1 if (r1 > entry) else r2
            tp = tp if tp else entry * 1.02

            trade["entry"] = entry
            trade["stop_loss"] = stop_loss
            trade["take_profit"] = tp

            reason_list.append(
                f"LONG: entry ≈ S1={entry:.2f}, SL < S2={stop_loss:.2f}, TP ≈ R1={tp:.2f}"
            )
        elif recommendation == "SHORT":
            entry = r1
            stop_loss = r2 * 1.02 if r2 else entry * 1.2
            tp = s1 if (s1 < entry) else s2
            tp = tp if tp else entry * 0.98

            trade["entry"] = entry
            trade["stop_loss"] = stop_loss
            trade["take_profit"] = tp

            reason_list.append(
                f"SHORT: entry ≈ R1={entry:.2f}, SL > R2={stop_loss:.2f}, TP ≈ S1={tp:.2f}"
            )
        else:
            reason_list.append("No trade suggested for NO_ACTION.")

        return trade, reason_list

    def _build_report(
        self,
        recommendation: str,
        overall_score: int,
        reason_list: List[str],
        sma_vals: Dict[str, float],
        rsi_1h: float,
        macd_1h_vals: Dict[str, float],
        local_highs: List[float],
        local_lows: List[float],
        suggested_trade: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Combine all info into a final report dict.
        """
        # Round out indicator values for readability
        indicator_values = {
            "sma50_4h": round(sma_vals.get("sma50_4h", 0), 2),
            "sma200_4h": round(sma_vals.get("sma200_4h", 0), 2),
            "rsi_1h": round(rsi_1h, 2),
            "macd_1h": round(macd_1h_vals["macd"], 2),
            "macd_signal_1h": round(macd_1h_vals["signal"], 2),
            "macd_hist_1h": round(macd_1h_vals["hist"], 2)
        }

        # Keep top 2 for clarity
        top_highs = [round(h, 2) for h in local_highs[:2]]
        top_lows = [round(l, 2) for l in local_lows[:2]]

        swing_levels = {
            "local_highs": top_highs,
            "local_lows": top_lows
        }

        if not top_highs or not top_lows:
            recommendation = "NO_ACTION"

        report = {
            "recommendation": recommendation,
            "overall_score": overall_score,
            "reason": reason_list,
            "indicator_values": indicator_values,
            "swing_levels": swing_levels,
            "suggested_trade": {
                "entry":    round(suggested_trade["entry"], 2) if suggested_trade["entry"] else None,
                "stop_loss":round(suggested_trade["stop_loss"], 2) if suggested_trade["stop_loss"] else None,
                "take_profit":round(suggested_trade["take_profit"], 2) if suggested_trade["take_profit"] else None
            }
        }
        return report
