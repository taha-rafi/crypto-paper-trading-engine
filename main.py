import sys
import time
from bot.engine import TradingEngine
from bot.market_data import MarketDataAdapter

def main():
    print("=========================================================")
    print("   QUANTITATIVE CRYPTO PAPER-TRADING PROTOTYPE ENGINE   ")
    print("=========================================================")
    
    symbol = "BTCUSDT"
    base_asset = "BTC"
    initial_cash = 10000.0
    
    print(f"Initializing Paper Trading Engine for {symbol} with ${initial_cash:.2f} virtual capital...")
    adapter = MarketDataAdapter()
    
    try:
        current_live_price = adapter.get_current_price(symbol)
        print(f"[LIVE MARKET DATA] {symbol} Current Price: ${current_live_price:,.2f}")
    except Exception as e:
        print(f"[NOTE] Live network query notice: {e}. Running in simulation mode.")
        current_live_price = 68500.0

    engine = TradingEngine(
        symbol=symbol,
        base_asset=base_asset,
        initial_cash=initial_cash,
        fast_period=3,
        slow_period=7,
        market_adapter=adapter
    )

    print("\n--- Running 10 Simulated Market Ticks with Dual-SMA Strategy ---")
    simulated_price_ticks = [
        current_live_price,
        current_live_price * 0.995,
        current_live_price * 0.990,
        current_live_price * 0.992,
        current_live_price * 0.998,
        current_live_price * 1.005,  # Upward inflection
        current_live_price * 1.015,  # Golden cross territory
        current_live_price * 1.025,
        current_live_price * 1.042,  # Take profit territory
        current_live_price * 1.035
    ]

    for idx, tick_price in enumerate(simulated_price_ticks, start=1):
        res = engine.tick(current_price=tick_price)
        action = res.get("action", "NONE")
        cash = res.get("cash", engine.broker.cash)
        holding = res.get("holding", 0.0)
        equity = res.get("equity", 10000.0)
        print(f"Tick {idx:02d} | Price: ${tick_price:,.2f} | Action: {action:<9} | Holdings: {holding:.4f} {base_asset} | Cash: ${cash:,.2f} | Equity: ${equity:,.2f}")

    print("\n=========================================================")
    print("                  FINAL TRADING LEDGER                   ")
    print("=========================================================")
    for t in engine.broker.trade_history:
        print(f"#{t['id']} [{t['action']}] {t['units']} {t['symbol']} @ ${t['price']:,.2f} | Fee: ${t['fee']:.2f} | Reason: {t['reason']}")
    print(f"\nFinal Portfolio Valuation: ${engine.broker.get_portfolio_value({base_asset: simulated_price_ticks[-1]}):,.2f}")
    print("Test run completed cleanly with zero real funds risked.")

if __name__ == "__main__":
    main()
