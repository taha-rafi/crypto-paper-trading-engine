import time
from typing import Dict, Any, List

class PaperBroker:
    """
    Virtual simulated execution broker.
    Maintains virtual balances, executes orders with realistic exchange fees,
    tracks realized/unrealized PnL, and records complete audit logs.
    """
    def __init__(self, initial_cash: float = 10000.0, fee_rate: float = 0.001):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.holdings: Dict[str, float] = {}       # e.g., {'BTC': 0.25}
        self.entry_prices: Dict[str, float] = {}   # Average entry price per asset
        self.fee_rate = fee_rate
        self.trade_history: List[Dict[str, Any]] = []

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        total = self.cash
        for asset, amount in self.holdings.items():
            price = current_prices.get(asset, 0.0)
            total += amount * price
        return round(total, 2)

    def execute_buy(self, symbol: str, units: float, price: float, reason: str = "") -> Dict[str, Any]:
        """
        Executes a paper BUY order.
        """
        if units <= 0 or price <= 0:
            return {"status": "REJECTED", "reason": "Invalid units or price"}

        cost = units * price
        fee = cost * self.fee_rate
        total_required = cost + fee

        if total_required > self.cash:
            return {
                "status": "REJECTED",
                "reason": f"Insufficient cash: required {total_required:.2f}, available {self.cash:.2f}"
            }

        # Deduct cash and add holdings
        self.cash -= total_required
        prev_units = self.holdings.get(symbol, 0.0)
        prev_cost = prev_units * self.entry_prices.get(symbol, 0.0)
        
        new_units = prev_units + units
        self.holdings[symbol] = round(new_units, 6)
        # Recalculate weighted average entry price
        self.entry_prices[symbol] = (prev_cost + cost) / new_units

        trade_record = {
            "id": len(self.trade_history) + 1,
            "timestamp": time.time(),
            "action": "BUY",
            "symbol": symbol,
            "units": units,
            "price": price,
            "cost": cost,
            "fee": fee,
            "remaining_cash": round(self.cash, 2),
            "reason": reason
        }
        self.trade_history.append(trade_record)
        return {"status": "FILLED", "trade": trade_record}

    def execute_sell(self, symbol: str, units: float, price: float, reason: str = "") -> Dict[str, Any]:
        """
        Executes a paper SELL order.
        """
        curr_units = self.holdings.get(symbol, 0.0)
        if units <= 0 or units > curr_units:
            return {
                "status": "REJECTED",
                "reason": f"Insufficient asset balance: requested {units}, available {curr_units}"
            }

        gross_proceeds = units * price
        fee = gross_proceeds * self.fee_rate
        net_proceeds = gross_proceeds - fee

        entry_price = self.entry_prices.get(symbol, price)
        realized_pnl = (price - entry_price) * units - fee

        self.cash += net_proceeds
        remaining_units = curr_units - units
        if remaining_units <= 1e-8:
            self.holdings.pop(symbol, None)
            self.entry_prices.pop(symbol, None)
        else:
            self.holdings[symbol] = round(remaining_units, 6)

        trade_record = {
            "id": len(self.trade_history) + 1,
            "timestamp": time.time(),
            "action": "SELL",
            "symbol": symbol,
            "units": units,
            "price": price,
            "net_proceeds": net_proceeds,
            "fee": fee,
            "realized_pnl": round(realized_pnl, 2),
            "remaining_cash": round(self.cash, 2),
            "reason": reason
        }
        self.trade_history.append(trade_record)
        return {"status": "FILLED", "trade": trade_record}
