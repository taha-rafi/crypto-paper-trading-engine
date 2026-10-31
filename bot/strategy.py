from typing import List, Dict, Any, Optional

class Signal:
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MovingAverageCrossStrategy:
    """
    Dual Moving Average Crossover Strategy with configurable fast & slow windows.
    Generates BUY when fast SMA crosses above slow SMA, and SELL when fast crosses below slow.
    """
    def __init__(self, fast_period: int = 5, slow_period: int = 15):
        if fast_period >= slow_period:
            raise ValueError("fast_period must be strictly less than slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period or period <= 0:
            return None
        return sum(prices[-period:]) / period

    def evaluate(self, historical_prices: List[float]) -> Dict[str, Any]:
        """
        Evaluates the price series and produces a signal along with indicator metrics.
        """
        if len(historical_prices) < self.slow_period + 1:
            return {
                "signal": Signal.HOLD,
                "reason": f"Insufficient price history (need {self.slow_period + 1}, got {len(historical_prices)})",
                "fast_sma": None,
                "slow_sma": None
            }

        # Current SMAs
        curr_fast = self.calculate_sma(historical_prices, self.fast_period)
        curr_slow = self.calculate_sma(historical_prices, self.slow_period)

        # Previous SMAs (one step prior)
        prev_prices = historical_prices[:-1]
        prev_fast = self.calculate_sma(prev_prices, self.fast_period)
        prev_slow = self.calculate_sma(prev_prices, self.slow_period)

        signal = Signal.HOLD
        reason = "No crossover detected"

        # Bullish Crossover: fast was below/equal slow, now above
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            signal = Signal.BUY
            reason = f"Bullish Golden Cross: Fast SMA ({curr_fast:.2f}) crossed above Slow SMA ({curr_slow:.2f})"
        # Bearish Crossover: fast was above/equal slow, now below
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            signal = Signal.SELL
            reason = f"Bearish Death Cross: Fast SMA ({curr_fast:.2f}) crossed below Slow SMA ({curr_slow:.2f})"

        return {
            "signal": signal,
            "reason": reason,
            "fast_sma": curr_fast,
            "slow_sma": curr_slow,
            "prev_fast_sma": prev_fast,
            "prev_slow_sma": prev_slow
        }
