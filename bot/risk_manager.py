import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Guards trading execution by enforcing quantitative risk limits:
    - Maximum allocation percentage per trade
    - Stop loss threshold
    - Take profit threshold
    - Maximum portfolio exposure
    """
    def __init__(
        self,
        max_allocation_pct: float = 0.10,     # Max 10% of portfolio per trade
        stop_loss_pct: float = 0.02,          # 2% stop-loss
        take_profit_pct: float = 0.04,        # 4% take-profit
        max_total_exposure_pct: float = 0.50  # Max 50% capital at risk
    ):
        self.max_allocation_pct = max_allocation_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_total_exposure_pct = max_total_exposure_pct

    def calculate_position_size(
        self,
        available_cash: float,
        total_portfolio_value: float,
        current_exposure_value: float,
        current_price: float
    ) -> float:
        """
        Determines the safe amount of asset to purchase based on risk constraints.
        Returns 0.0 if limits are exceeded.
        """
        if current_price <= 0:
            return 0.0

        # Check total exposure cap
        allowed_exposure = total_portfolio_value * self.max_total_exposure_pct
        if current_exposure_value >= allowed_exposure:
            logger.info("Risk limit reached: Maximum portfolio exposure reached.")
            return 0.0

        # Max budget for this trade
        trade_budget = min(
            total_portfolio_value * self.max_allocation_pct,
            available_cash,
            allowed_exposure - current_exposure_value
        )

        if trade_budget <= 0:
            return 0.0

        units = trade_budget / current_price
        return round(units, 6)

    def check_exit_triggers(
        self,
        entry_price: float,
        current_price: float
    ) -> Optional[str]:
        """
        Checks whether stop loss or take profit conditions are met.
        Returns 'STOP_LOSS', 'TAKE_PROFIT', or None.
        """
        if entry_price <= 0 or current_price <= 0:
            return None

        pnl_pct = (current_price - entry_price) / entry_price

        if pnl_pct <= -self.stop_loss_pct:
            return "STOP_LOSS"
        elif pnl_pct >= self.take_profit_pct:
            return "TAKE_PROFIT"

        return None
