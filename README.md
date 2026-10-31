# Quantitative Crypto Paper-Trading Engine

A robust, testable, and modular Python framework for paper-trading cryptocurrency pairs with automated market data ingestion, quantitative indicator strategies, strict risk governance, and virtual trade accounting.

Developed by **Taha Rafi** ([GitHub](https://github.com/taha-rafi) · [Portfolio](https://taharafi.com)).

---

## 🌟 Key Features

1. **Zero-Deposit & Safe Execution**: Operates purely in paper-trading simulation mode with virtual capital ($10,000 USD default). Zero real funds or private keys required.
2. **Live Market Data Adapter**: Ingests real-time prices and OHLCV klines from public exchange endpoints (Binance REST API) with resilient error handling and network fallback.
3. **Quantitative Strategy Engine**: Implements configurable Dual Moving Average Crossover (`Fast SMA` vs `Slow SMA`) with mathematically verified Golden Cross (BUY) and Death Cross (SELL) signal generation.
4. **Institutional Risk Governance**:
   - **Position Sizing Cap**: Limits maximum exposure per trade (default 10% of total portfolio equity).
   - **Total Portfolio Exposure Ceiling**: Caps gross market exposure at 50% to prevent over-allocation.
   - **Automated Stop-Loss**: Triggers position liquidation if unrealized loss reaches 2%.
   - **Automated Take-Profit**: Locks in gains when unrealized profit reaches 4%.
5. **Simulated Broker & Ledger**: Accurately tracks virtual cash balances, asset inventories, average entry prices, realistic exchange fees (0.1%), and generates an immutable audit log.
6. **100% Test Coverage**: Full `unittest` suite testing insufficient cash, repeated signals, network dropouts, risk ceiling breaches, and order execution math.

---

## 📂 Architecture

```text
paper-trading-bot/
├── bot/
│   ├── __init__.py           # Package exports
│   ├── market_data.py        # Public exchange data adapter
│   ├── strategy.py           # Dual-SMA crossover signal logic
│   ├── risk_manager.py       # Capital preservation & position sizing
│   ├── simulator.py          # Virtual broker, ledger & fee accounting
│   └── engine.py             # Main cycle loop coordinator
├── tests/
│   └── test_trading_bot.py   # Comprehensive unit test suite
├── main.py                   # Live demo runner
└── README.md                 # Technical documentation
```

---

## 🚀 Quickstart

### 1. Run the Live Demonstration
```bash
python main.py
```

### 2. Run the Unit Test Suite
```bash
python -m unittest discover tests
```

---

## 🧪 Unit Test Verification Summary

All 9 test cases pass in sub-second time:
- `test_position_sizing_within_limits`: Verifies 10% equity sizing cap.
- `test_max_total_exposure_breach`: Rejects trades when portfolio exposure reaches limit.
- `test_insufficient_balance_rejection`: Rejects orders exceeding available cash.
- `test_stop_loss_trigger`: Validates automated stop-loss execution at -2%.
- `test_take_profit_trigger`: Validates automated profit taking at +4%.
- `test_strategy_crossover_signal`: Verifies Golden Cross signal generation.
- `test_no_double_buy_when_capital_exhausted`: Guards against duplicate buys on signal repetition.
- `test_failed_api_response_handling`: Confirms graceful recovery on network downtime.
- `test_full_lifecycle_simulation`: Tests buy fill, cost basis calculation, sell fill, fee deductions, and net PnL accounting.
