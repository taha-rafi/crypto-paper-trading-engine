import unittest
from unittest.mock import MagicMock
from bot.market_data import MarketDataAdapter
from bot.strategy import MovingAverageCrossStrategy, Signal
from bot.risk_manager import RiskManager
from bot.simulator import PaperBroker
from bot.engine import TradingEngine

class TestTradingBot(unittest.TestCase):

    def setUp(self):
        self.risk_manager = RiskManager(
            max_allocation_pct=0.10,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
            max_total_exposure_pct=0.50
        )
        self.broker = PaperBroker(initial_cash=10000.0, fee_rate=0.001)

    # 1. Test Position Sizing & Max Allocation
    def test_position_sizing_within_limits(self):
        # 10% of 10000 = 1000 USD budget. At price 50000 -> 0.02 BTC
        size = self.risk_manager.calculate_position_size(
            available_cash=10000.0,
            total_portfolio_value=10000.0,
            current_exposure_value=0.0,
            current_price=50000.0
        )
        self.assertEqual(size, 0.02)

    # 2. Test Maximum Total Exposure Cap
    def test_max_total_exposure_breach(self):
        # Exposure is already at 50% (5000 USD). Should return 0.0 units
        size = self.risk_manager.calculate_position_size(
            available_cash=5000.0,
            total_portfolio_value=10000.0,
            current_exposure_value=5000.0,
            current_price=50000.0
        )
        self.assertEqual(size, 0.0)

    # 3. Test Insufficient Balance Rejection
    def test_insufficient_balance_rejection(self):
        broker = PaperBroker(initial_cash=100.0)
        # Attempt to buy 1 BTC at 50,000 USD (needs >50,000 USD)
        result = broker.execute_buy("BTC", units=1.0, price=50000.0)
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("Insufficient cash", result["reason"])
        self.assertEqual(broker.cash, 100.0)
        self.assertEqual(len(broker.holdings), 0)

    # 4. Test Stop-Loss Trigger
    def test_stop_loss_trigger(self):
        entry_price = 50000.0
        # 2% stop-loss triggers at or below 49,000.0
        trigger = self.risk_manager.check_exit_triggers(entry_price=entry_price, current_price=48900.0)
        self.assertEqual(trigger, "STOP_LOSS")

    # 5. Test Take-Profit Trigger
    def test_take_profit_trigger(self):
        entry_price = 50000.0
        # 4% take-profit triggers at or above 52,000.0
        trigger = self.risk_manager.check_exit_triggers(entry_price=entry_price, current_price=52100.0)
        self.assertEqual(trigger, "TAKE_PROFIT")

    # 6. Test Moving Average Crossover Strategy Evaluation
    def test_strategy_crossover_signal(self):
        strat = MovingAverageCrossStrategy(fast_period=3, slow_period=5)
        # Build price series where fast crosses above slow
        # Initial prices keeping fast below slow
        prices = [100.0, 100.0, 100.0, 100.0, 100.0, 95.0, 90.0, 85.0]
        # Spike up to cross above
        prices.extend([110.0, 120.0, 130.0])
        eval_res = strat.evaluate(prices)
        self.assertIn(eval_res["signal"], [Signal.BUY, Signal.HOLD])
        self.assertIsNotNone(eval_res["fast_sma"])
        self.assertIsNotNone(eval_res["slow_sma"])

    # 7. Test Repeated Signals Prevention & Holding Check
    def test_no_double_buy_when_capital_exhausted(self):
        engine = TradingEngine(initial_cash=500.0)
        # Artificially simulate BUY fill
        engine.broker.cash = 0.0
        res = engine.tick(current_price=50000.0)
        # Cash is <= 10.0, so no BUY execution takes place
        self.assertEqual(res.get("action"), "NONE")

    # 8. Test Failed Market Data Handling (Network Fault Tolerance)
    def test_failed_api_response_handling(self):
        mock_adapter = MagicMock()
        mock_adapter.get_current_price.side_effect = ConnectionError("Connection refused: 503")
        engine = TradingEngine(market_adapter=mock_adapter)
        res = engine.tick()
        self.assertEqual(res["status"], "ERROR")
        self.assertIn("Connection refused", res["message"])

    # 9. Test Full End-to-End Simulation Lifecycle
    def test_full_lifecycle_simulation(self):
        broker = PaperBroker(initial_cash=10000.0, fee_rate=0.001)
        # 1. Buy 0.1 BTC @ 50,000 (Cost = 5000 + 5 fee = 5005)
        buy_res = broker.execute_buy("BTC", 0.1, 50000.0, reason="Test Buy")
        self.assertEqual(buy_res["status"], "FILLED")
        self.assertAlmostEqual(broker.cash, 4995.0, places=2)
        self.assertEqual(broker.holdings["BTC"], 0.1)

        # 2. Sell 0.1 BTC @ 55,000 (Gross = 5500, fee = 5.5, Net = 5494.5)
        sell_res = broker.execute_sell("BTC", 0.1, 55000.0, reason="Test Take Profit")
        self.assertEqual(sell_res["status"], "FILLED")
        self.assertAlmostEqual(broker.cash, 4995.0 + 5494.5, places=2)
        self.assertNotIn("BTC", broker.holdings)
        self.assertGreater(sell_res["trade"]["realized_pnl"], 400.0)

if __name__ == "__main__":
    unittest.main()
