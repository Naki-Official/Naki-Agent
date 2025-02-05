import json
import numpy as np
import talib
import logging
from typing import List, Optional, Dict, Any

from phi.tools import Toolkit
from agents.tools.cryptocompare import CryptoCompareTools

logger = logging.getLogger(__name__)

class TechnicalAnalysisToolkit(Toolkit):
    """
    The TechnicalAnalysisToolkit provides methods for performing technical chart analysis on
    crypto coins using common indicators. It leverages TA‑Lib for indicator computation and
    uses CryptoCompareTools to fetch OHLCV data.
    """
    
    def __init__(self, COMPARE_CRYPTO_API_KEY: Optional[str] = None):
        """
        Initialize the Technical Analysis Toolkit.

        Args:
            COMPARE_CRYPTO_API_KEY (Optional[str]): API key for CryptoCompare.
        """
        super().__init__(name="technical_analysis")
        self.cc_tools = CryptoCompareTools(api_key=COMPARE_CRYPTO_API_KEY)
        # Register analysis functions if desired.
        self.register(self.get_ohlcv)
        self.register(self.sma)
        self.register(self.ema)
        self.register(self.rsi)
        self.register(self.macd)
        self.register(self.bollinger_bands)
    
    def get_ohlcv(self, from_symbol: str = 'btc', to_symbol: str = 'usd', aggregate: int = 30) -> Dict:
        """
        Retrieve OHLCV data using CryptoCompareTools.

        Args:
            from_symbol (str): The coin symbol (e.g., 'btc').
            to_symbol (str): The currency symbol (e.g., 'usd').
            aggregate (int): Aggregate minutes per data point.

        Returns:
            Dict: A dictionary with keys 'time', 'open', 'high', 'low', 'close', and 'volume'.
        """
        ohlcv_json = self.cc_tools.historical_ohlcv_minute(from_symbol, to_symbol, aggregate)
        data = json.loads(ohlcv_json)
        # Sort data by time in ascending order.
        data = sorted(data, key=lambda x: x["time"])
        times = [d["time"] for d in data]
        opens = np.array([d["open"] for d in data], dtype=float)
        highs = np.array([d["high"] for d in data], dtype=float)
        lows = np.array([d["low"] for d in data], dtype=float)
        closes = np.array([d["close"] for d in data], dtype=float)
        # We use "volumeto" as the volume (in USD)
        volumes = np.array([d.get("volumeto", 0) for d in data], dtype=float)
        return {
            "time": times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        }
    
    def sma(self, data: Dict, timeperiod: int = 14) -> List[float]:
        """
        Compute the Simple Moving Average (SMA) of closing prices.
        """
        closes = data["close"]
        sma_values = talib.SMA(closes, timeperiod=timeperiod)
        return sma_values.tolist()
    
    def ema(self, data: Dict, timeperiod: int = 14) -> List[float]:
        """
        Compute the Exponential Moving Average (EMA) of closing prices.
        """
        closes = data["close"]
        ema_values = talib.EMA(closes, timeperiod=timeperiod)
        return ema_values.tolist()
    
    def rsi(self, data: Dict, timeperiod: int = 14) -> List[float]:
        """
        Compute the Relative Strength Index (RSI) of closing prices.
        """
        closes = data["close"]
        rsi_values = talib.RSI(closes, timeperiod=timeperiod)
        return rsi_values.tolist()
    
    def macd(self, data: Dict, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> Dict:
        """
        Compute the Moving Average Convergence Divergence (MACD) of closing prices.
        """
        closes = data["close"]
        macd_vals, macd_signal, macd_hist = talib.MACD(closes,
                                                       fastperiod=fastperiod,
                                                       slowperiod=slowperiod,
                                                       signalperiod=signalperiod)
        return {
            "macd": macd_vals.tolist(),
            "macdsignal": macd_signal.tolist(),
            "macdhist": macd_hist.tolist()
        }
    
    def bollinger_bands(self, data: Dict, timeperiod: int = 20, nbdevup: float = 2, nbdevdn: float = 2) -> Dict:
        """
        Compute Bollinger Bands for the closing prices.
        """
        closes = data["close"]
        upperband, middleband, lowerband = talib.BBANDS(closes,
                                                        timeperiod=timeperiod,
                                                        nbdevup=nbdevup,
                                                        nbdevdn=nbdevdn,
                                                        matype=0)
        return {
            "upperband": upperband.tolist(),
            "middleband": middleband.tolist(),
            "lowerband": lowerband.tolist()
        }
    
    def _parse_ohlcv(self, ohlcv_json: str) -> Dict[str, Any]:
        """
        Parse OHLCV JSON data (assumed to be in the returned list) into a dictionary of NumPy arrays.
        """
        data = json.loads(ohlcv_json)
        data = sorted(data, key=lambda x: x["time"])
        times = [d["time"] for d in data]
        opens = np.array([d["open"] for d in data], dtype=float)
        highs = np.array([d["high"] for d in data], dtype=float)
        lows = np.array([d["low"] for d in data], dtype=float)
        closes = np.array([d["close"] for d in data], dtype=float)
        volumes = np.array([d.get("volumeto", 0) for d in data], dtype=float)
        return {"time": times, "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes}
    
    def _compute_pivot_levels(self, high: float, low: float, close: float) -> Dict[str, float]:
        """
        Calculate pivot, support, and resistance levels from a single candle.
        """
        pivot = (high + low + close) / 3.0
        support = 2 * pivot - high
        resistance = 2 * pivot - low
        return {"pivot": pivot, "support": support, "resistance": resistance}
    
    def comprehensive_ta_analysis(
        self,
        from_symbol: str = "btc",
        to_symbol: str = "usd",
        fourh_limit: int = 200,   # Up to ~200 x 4h = 800 hours (~33 days)
        hour_limit: int = 100,    # Up to ~100 hours (~4 days) for immediate signals
        lookback_for_swing: int = 50  # Number of 4h bars to scan for swing highs/lows
    ) -> str:
        """
        Perform a comprehensive technical analysis using 4-hour data for the main trend
        and 1-hour data for immediate signals. Instead of pivot points, we use
        swing highs/lows to define support/resistance.

        Key points:
        - 4-hour data: major trend (SMA50 vs. SMA200) + find recent local maxima/minima as S/R
        - 1-hour data: RSI & MACD for immediate momentum signals
        - A simple scoring system to produce a recommendation (LONG, SHORT, or NO_ACTION)
        - Wider stops and TPs suitable for multi-day holds

        Args:
            from_symbol (str): Base symbol (e.g., "btc")
            to_symbol (str): Quote symbol (e.g., "usd")
            fourh_limit (int): Number of 4h candles to retrieve for mid-term analysis
            hour_limit (int): Number of 1h candles for short-term signals
            lookback_for_swing (int): Number of recent 4h bars to scan for local maxima/minima

        Returns:
            str: A JSON-formatted string containing:
                - recommendation: "LONG", "SHORT", or "NO_ACTION"
                - overall_score
                - reason: Explanation of how we arrived at that recommendation
                - indicator_values: final readings (SMA50_4h, SMA200_4h, RSI_1h, MACD_1h, etc.)
                - swing_levels: extracted from local maxima/minima
                - suggested_trade: entry, stop_loss, take_profit
        """
        import json
        import talib
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info(
                "Starting mid-term TA analysis for %s/%s using 4h & 1h data (swing highs/lows).",
                from_symbol, to_symbol
            )

            # ======================================================================
            # (1) 4-Hour Data -> major trend + find local maxima/minima
            # ======================================================================
            fourh_json = self.cc_tools.historical_ohlcv_hour(
                from_symbol, to_symbol,
                limit=fourh_limit,
                aggregate=4  # each candle = 4 hours
            )
            fourh_data = self._parse_ohlcv(fourh_json)
            f_closes = fourh_data["close"]
            f_highs  = fourh_data["high"]
            f_lows   = fourh_data["low"]

            if len(f_closes) < 200:
                raise ValueError("Not enough 4-hour data to compute SMA200 for mid-term trend.")

            # -- 1.1) Trend: use SMA50 vs. SMA200 on 4-hour data
            sma50_4h = talib.SMA(f_closes, timeperiod=50)
            sma200_4h = talib.SMA(f_closes, timeperiod=200)
            last_sma50_4h = sma50_4h[-1] if sma50_4h[-1] is not None else 0.0
            last_sma200_4h = sma200_4h[-1] if sma200_4h[-1] is not None else 0.0
            mid_trend = "bullish" if last_sma50_4h > last_sma200_4h else "bearish"

            # -- 1.2) Find local maxima (resistance) / minima (support) in the last X bars
            # We'll scan the last `lookback_for_swing` 4h bars
            # A bar i is a local max if: high[i] > high[i-1] and high[i] > high[i+1]
            # Similarly, a local min if: low[i] < low[i-1] and low[i] < low[i+1]

            def find_swing_highs_lows(highs, lows, window: int):
                """
                Return two sorted lists:
                - local_highs (descending order)
                - local_lows  (ascending order)
                from the last `window` bars (excluding the final bar if you want 'confirmed' swing).
                """
                local_highs = []
                local_lows = []
                start_idx = max(1, len(highs) - window)  # to ensure i-1 is valid
                end_idx = len(highs) - 1                 # up to second-last to check i+1

                for i in range(start_idx, end_idx):
                    if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                        local_highs.append(highs[i])
                    if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                        local_lows.append(lows[i])

                # Sort descending for highs, ascending for lows
                local_highs.sort(reverse=True)
                local_lows.sort()
                return local_highs, local_lows

            local_highs, local_lows = find_swing_highs_lows(f_highs, f_lows, lookback_for_swing)

            # We'll pick top 2 resistances and top 2 supports
            # If we don't have enough data, fallback to partial
            r1 = local_highs[0] if len(local_highs) > 0 else None
            r2 = local_highs[1] if len(local_highs) > 1 else None
            s1 = local_lows[0]  if len(local_lows) > 0 else None
            s2 = local_lows[1]  if len(local_lows) > 1 else None

            # If there's missing data, just fill with None or 0
            # or we can fallback to the final bar's high/low if needed
            if r1 is None: r1 = max(f_highs[-lookback_for_swing:])
            if r2 is None: r2 = max(f_highs[-lookback_for_swing:])
            if s1 is None: s1 = min(f_lows[-lookback_for_swing:])
            if s2 is None: s2 = min(f_lows[-lookback_for_swing:])

            # ======================================================================
            # (2) 1-Hour Data -> immediate signals (RSI, MACD)
            # ======================================================================
            hour_json = self.cc_tools.historical_ohlcv_hour(
                from_symbol, to_symbol,
                limit=hour_limit,
                aggregate=1
            )
            hour_data = self._parse_ohlcv(hour_json)
            h_closes = hour_data["close"]

            if len(h_closes) < 26:
                raise ValueError("Not enough 1-hour data to compute MACD(12,26).")

            # RSI(14) on 1-hour
            rsi_1h_vals = talib.RSI(h_closes, timeperiod=14)
            latest_rsi_1h = rsi_1h_vals[-1]

            # MACD(12,26,9) on 1-hour
            macd_vals, macd_signal, macd_hist = talib.MACD(h_closes, fastperiod=12, slowperiod=26, signalperiod=9)
            latest_macd_1h = macd_vals[-1]
            latest_macd_signal_1h = macd_signal[-1]
            latest_macd_hist_1h = macd_hist[-1]

            # ======================================================================
            # (3) Build Score + Reason
            # ======================================================================
            overall_score = 0
            reason_list = []

            # 4h trend
            if mid_trend == "bullish":
                overall_score += 1
                reason_list.append("4h trend: SMA50_4h > SMA200_4h (bullish).")
            else:
                overall_score -= 1
                reason_list.append("4h trend: SMA50_4h <= SMA200_4h (bearish).")

            # RSI (1-hour)
            if latest_rsi_1h < 30:
                overall_score += 1
                reason_list.append(f"RSI(14,1h) oversold at {latest_rsi_1h:.2f}.")
            elif latest_rsi_1h > 70:
                overall_score -= 1
                reason_list.append(f"RSI(14,1h) overbought at {latest_rsi_1h:.2f}.")
            else:
                reason_list.append(f"RSI(14,1h) neutral at {latest_rsi_1h:.2f}.")

            # MACD histogram (1-hour)
            if latest_macd_hist_1h > 0:
                overall_score += 1
                reason_list.append("MACD(1h) histogram positive -> bullish momentum.")
            else:
                overall_score -= 1
                reason_list.append("MACD(1h) histogram negative -> bearish momentum.")

            # ======================================================================
            # (4) Recommendation
            # ======================================================================
            if overall_score >= 2:
                recommendation = "LONG"
                reason_list.append("Overall score >= 2 -> LONG signal.")
            elif overall_score <= -2:
                recommendation = "SHORT"
                reason_list.append("Overall score <= -2 -> SHORT signal.")
            else:
                recommendation = "NO_ACTION"
                reason_list.append("Score is in [-1,1] -> NO_ACTION.")

            # ======================================================================
            # (5) Suggest Entry, SL, TP using swing highs/lows
            # ======================================================================
            suggested_trade = {
                "entry": None,
                "stop_loss": None,
                "take_profit": None
            }

            # We'll define a simple approach:
            #   If LONG:
            #       entry near S1
            #       stop_loss near S2 (some offset below)
            #       take_profit near R1 (or fallback R2 if R1 < entry)
            #   If SHORT:
            #       entry near R1
            #       stop_loss near R2 (some offset above)
            #       take_profit near S1 (or fallback S2 if S1 > entry)
            # You can refine offsets, or pick average of multiple swing levels.

            if recommendation == "LONG":
                entry = s1 if s1 else 0
                stop_loss = (s2 * 0.98) if s2 else (entry * 0.98)
                take_profit = r1 if r1 and r1 > entry else (r2 if r2 else entry * 1.02)
                suggested_trade["entry"] = entry
                suggested_trade["stop_loss"] = stop_loss
                suggested_trade["take_profit"] = take_profit
                reason_list.append(
                    f"LONG: entry ≈ S1={entry:.2f}, SL < S2={stop_loss:.2f}, TP ≈ R1={take_profit:.2f}"
                )
            elif recommendation == "SHORT":
                entry = r1 if r1 else 999999  # fallback
                stop_loss = (r2 * 1.02) if r2 else (entry * 1.02)
                take_profit = s1 if s1 and s1 < entry else (s2 if s2 else entry * 0.98)
                suggested_trade["entry"] = entry
                suggested_trade["stop_loss"] = stop_loss
                suggested_trade["take_profit"] = take_profit
                reason_list.append(
                    f"SHORT: entry ≈ R1={entry:.2f}, SL > R2={stop_loss:.2f}, TP ≈ S1={take_profit:.2f}"
                )
            else:
                reason_list.append("No trade suggested due to NO_ACTION.")

            # ======================================================================
            # (6) Build final report
            # ======================================================================
            indicator_values = {
                "sma50_4h": round(last_sma50_4h, 2),
                "sma200_4h": round(last_sma200_4h, 2),
                "rsi_1h": round(latest_rsi_1h, 2),
                "macd_1h": round(latest_macd_1h, 2),
                "macd_signal_1h": round(latest_macd_signal_1h, 2),
                "macd_hist_1h": round(latest_macd_hist_1h, 2)
            }

            # We'll store the top 2 local highs/lows we found:
            swing_levels = {
                "local_highs": [round(h, 2) for h in local_highs[:2]],  # top 2 highest
                "local_lows":  [round(l, 2) for l in local_lows[:2]]   # top 2 lowest
            }

            report = {
                "recommendation": recommendation,
                "overall_score": overall_score,
                "reason": reason_list,
                "indicator_values": indicator_values,
                "swing_levels": swing_levels,
                "suggested_trade": suggested_trade
            }

            return json.dumps(report, indent=2)

        except Exception as e:
            logger.error("Error in mid-term TA analysis (swing highs/lows): %s", e)
            return json.dumps({"error": str(e)})