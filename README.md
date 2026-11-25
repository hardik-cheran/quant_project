# Market Making Simulator

A Python-based electronic market-making simulator that models a limit order book, order execution, inventory management, and market-maker P&L.

The project explores how a market maker interacts with incoming order flow, manages inventory risk, and adjusts bid and ask quotes as market conditions change.

## Features

### 1. Limit Order Book
- Separate bid and ask sides.
- Price-time priority.
- FIFO execution at each price level.
- Support for limit buy and limit sell orders.
- Best bid, best ask, and mid-price tracking.

### 2. Order Execution
- Market buy and market sell orders.
- Partial order fills.
- Order cancellation.
- Order lifecycle and execution reports.
- Self-trade prevention.

### 3. Market Maker
- Dynamic bid and ask quote placement.
- Inventory-aware quote skewing.
- Configurable maximum inventory.
- Cancellation and replacement of previous quotes.
- Prevention of quotes crossing the external market.

### 4. Market Simulation
- Random market order flow.
- Random-walk reference price.
- Refreshing external bid and ask liquidity.
- Simulation over multiple time steps.

### 5. P&L and Risk Tracking
- Cash and inventory tracking.
- Average inventory cost.
- Realized P&L.
- Unrealized P&L.
- Total mark-to-market P&L.

## Project Structure

```text
quant_project/
│
├── OrderBook.py
├── test_orderbook.py
└── README.md
```

## Getting Started

### Requirements

- Python 3
- Standard Python libraries

### Run the simulator

```bash
python3 OrderBook.py
```

### Run the tests

```bash
python3 -m unittest -v test_orderbook.py
```

## Current Development Status

The simulator currently implements the core order-book engine, order matching, a basic inventory-aware market-making strategy, and a stochastic market environment.

The project is under active development.

## Future Improvements

- More realistic market order flow.
- Improved volatility estimation.
- Adverse selection analysis.
- More sophisticated inventory and quote management.
- Performance and risk analysis across multiple simulation runs.
- Strategy evaluation under different market conditions.

## Motivation

This project is an exploration of electronic trading, market microstructure, and quantitative market-making strategies, with an emphasis on understanding the mechanics of limit order books and inventory risk.