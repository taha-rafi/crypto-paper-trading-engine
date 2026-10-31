import logging
import time
from typing import Dict, Any, Optional
from .market_data import MarketDataAdapter
from .strategy import MovingAverageCrossStrategy, Signal
from .risk_manager import RiskManager
from .simulator import PaperBroker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TradingEngine")

class TradingEngine:
    """
    Main engine orchestrating market data ingestion, strategy signal evaluation,
    risk governance checks, and simulated execution.
    """
    def __init__(
        self,
        symbol: str = "BTCUSDT",
        base_asset: str = "BTC",
        initial_cash: float = 10000.0,
        fast_period: int = 5,
        slow_period: int = 15,
        market_adapter: Optional[MarketDataAdapter] = None
    ):
        self.symbol = symbol
        self.base_asset = base_asset
        self.market_adapter = market_adapter or MarketDataAdapter()
        self.strategy = MovingAverageCrossStrategy(fast_period=fast_period, slow_period=slow_period)
        self.risk_manager = RiskManager()
        self.broker = PaperBroker(initial_cash=initial_cash)
        self.price_history: list[float] = []

    def tick(self, current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Executes a single cycle of the trading engine:
        1. Ingest price
        2. Check existing position stop-loss / take-profit
        3. Evaluate strategy signal
        4. Size position via risk manager
        5. Execute simulated order
        """
        if current_price is None:
            try:
                current_price = self.market_adapter.get_current_price(self.symbol)
            except Exception as e:
                logger.error(f"Failed to fetch market price for {self.symbol}: {e}")
                return {"status": "ERROR", "message": str(e)}

        self.price_history.append(current_price)
        current_prices = {self.base_asset: current_price}
        total_equity = self.broker.get_portfolio_value(current_prices)
        current_holding = self.broker.holdings.get(self.base_asset, 0.0)
        current_exposure = current_holding * current_price

        # Check exit triggers (Stop-Loss / Take-Profit)
        if current_holding > 0:
            entry_price = self.broker.entry_prices.get(self.base_asset, current_price)
            exit_trigger = self.risk_manager.check_exit_triggers(entry_price, current_price)
            if exit_trigger:
                reason = f"Risk Exit: {exit_trigger} triggered at {current_price:.2f} (Entry: {entry_price:.2f})"
                logger.info(reason)
                fill = self.broker.execute_sell(self.base_asset, current_holding, current_price, reason=reason)
                return {
                    "action": "RISK_EXIT",
                    "trigger": exit_trigger,
                    "fill": fill,
                    "equity": self.broker.get_portfolio_value(current_prices)
                }

        # Evaluate strategy
        eval_result = self.strategy.evaluate(self.price_history)
        signal = eval_result.get("signal")
        reason = eval_result.get("reason")

        execution_result = {"action": "NONE", "signal": signal, "reason": reason}

        if signal == Signal.BUY and self.broker.cash > 10.0:
            units = self.risk_manager.calculate_position_size(
                available_cash=self.broker.cash,
                total_portfolio_value=total_equity,
                current_exposure_value=current_exposure,
                current_price=current_price
            )
            if units > 0:
                logger.info(f"Signal BUY: Sizing {units} {self.base_asset} @ {current_price}")
                fill = self.broker.execute_buy(self.base_asset, units, current_price, reason=reason)
                execution_result = {"action": "BUY", "units": units, "fill": fill}

        elif signal == Signal.SELL and current_holding > 0:
            logger.info(f"Signal SELL: Liquidating {current_holding} {self.base_asset} @ {current_price}")
            fill = self.broker.execute_sell(self.base_asset, current_holding, current_price, reason=reason)
            execution_result = {"action": "SELL", "units": current_holding, "fill": fill}

        execution_result["equity"] = self.broker.get_portfolio_value(current_prices)
        execution_result["cash"] = self.broker.cash
        execution_result["holding"] = self.broker.holdings.get(self.base_asset, 0.0)
        return execution_result
