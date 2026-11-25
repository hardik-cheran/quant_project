import random
import heapq
from collections import deque
import matplotlib.pyplot as plt


class RandomTrader:
    def __init__(self, trader_id):
        self.trader_id = trader_id

    def step(self, book):
        r = random.random()
        mid = book.mid_price()
        if mid is None:
            mid = 100
        price = round(random.gauss(mid, 2))
        quantity = random.randint(1,10)

        if r < 0.35:
            action = "limit_buy"
        elif r < 0.7:
            action = "limit_sell"
        elif r < 0.80:
            action = "market_buy"
        elif r < 0.90:
            action = "market_sell"
        else :
            action = "cancel_order:"

        if action == "limit_buy":
            book.add_limit_buy(price,quantity,self.trader_id)

        elif action == "limit_sell":
            book.add_limit_sell(price,quantity, self.trader_id)

        elif action == "market_buy":
            book.market_buy(quantity, self.trader_id)

        elif action == "market_sell":
            book.market_sell(quantity, self.trader_id)
        else:
            if book.order_map:
                order_id = random.choice(list(book.order_map.keys()))
                book.cancel_order(order_id,self.trader_id)

class Order:
    def __init__(self, order_id, trader_id,side, price, quantity):
        self.order_id = order_id
        self.trader_id = trader_id
        self.side = side
        self.price = price
        self.quantity = quantity
        self.status = "NEW"
        self.filled_quantity = 0
        self.original_quantity = quantity


    def __repr__(self):
        return f"Order(id={self.order_id}, trader={self.trader_id}, qty={self.quantity})"


class OrderBook:
    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.bid_heap = []
        self.ask_heap = []
        self.next_order_id = 1
        self.trade_history = []
        self.traders = {}
        self.order_map = {}
        self.order_history = {}

    
    def validate_order_book(self):

     active_orders = {}

    # Collect all active buy orders
     for price, orders in self.bids.items():
        for order in orders:

            assert order.side == "BUY"
            assert order.price == price
            assert order.quantity > 0
            assert order.status in ("RESTING", "PARTIALLY_FILLED")

            active_orders[order.order_id] = order

    # Collect all active sell orders
     for price, orders in self.asks.items():
        for order in orders:

            assert order.side == "SELL"
            assert order.price == price
            assert order.quantity > 0
            assert order.status in ("RESTING", "PARTIALLY_FILLED")

            active_orders[order.order_id] = order

    # Check active order map
     assert set(active_orders.keys()) == set(self.order_map.keys())

     for order_id, order in self.order_map.items():

        assert order_id == order.order_id
        assert order_id in self.order_history
        assert self.order_history[order_id] is order

    # Check order history
     for order_id, order in self.order_history.items():

        assert order_id == order.order_id
        assert order.original_quantity == (
            order.filled_quantity + order.quantity
        )

        assert order.quantity >= 0
        assert order.filled_quantity >= 0

        if order.status == "FILLED":
            assert order.quantity == 0

    # Check that the book is not crossed
     best_bid = self.best_bid()
     best_ask = self.best_ask()

     if best_bid is not None and best_ask is not None:
        assert best_bid < best_ask, (
            f"Crossed book: best bid {best_bid}, "
            f"best ask {best_ask}"
        )

     return True

 
    def add_limit_buy(self, price, quantity, trader_id):

     requested_quantity = quantity
     filled_quantity = 0
     total_value = 0

    # 1. Create the incoming order immediately
     order = Order(
        self.next_order_id,
        trader_id,
        "BUY",
        price,
        quantity
    )

     order_id = order.order_id
     self.next_order_id += 1

    # Every submitted order is recorded, even if fully filled
     self.order_history[order_id] = order

    # 2. Match against the ask book
     while order.quantity > 0 and self.asks:

        best_ask = self.best_ask()

        if best_ask is None or best_ask > price:
            break

        oldest_order = self.asks[best_ask][0]

        # Self-trade prevention
        if oldest_order.trader_id == trader_id:
            print("Self-trade prevention: incoming buy order canceled")

            order.status = "CANCELED"

            average_price = (
                total_value / filled_quantity
                if filled_quantity > 0 else 0
            )

            return {
                "requested_quantity": requested_quantity,
                "filled_quantity": filled_quantity,
                "remaining_quantity": order.quantity,
                "average_execution_price": average_price,
                "order_id": order_id,
                "status": "CANCELED"
            }

        # 3. Execute the trade
        traded_quantity = min(
            order.quantity,
            oldest_order.quantity
        )

        print(f"TRADE: {traded_quantity} @ {best_ask}")

        self.record_trade(
            best_ask,
            traded_quantity,
            trader_id,
            oldest_order.trader_id
        )

        # Update incoming order
        order.quantity -= traded_quantity
        order.filled_quantity += traded_quantity

        # Update resting order
        oldest_order.quantity -= traded_quantity
        oldest_order.filled_quantity += traded_quantity

        filled_quantity += traded_quantity
        total_value += traded_quantity * best_ask

        # Update resting order status
        if oldest_order.quantity == 0:
            oldest_order.status = "FILLED"
        else:
            oldest_order.status = "PARTIALLY_FILLED"

        # 4. Remove fully filled resting orders
        if oldest_order.quantity == 0:

            filled_order = self.asks[best_ask].popleft()

            del self.order_map[filled_order.order_id]

            if not self.asks[best_ask]:
                del self.asks[best_ask]

    # 5. Add remaining quantity to the book
     if order.quantity > 0:

        if order.filled_quantity > 0:
            order.status = "PARTIALLY_FILLED"
        else:
            order.status = "RESTING"

        self.order_map[order_id] = order

        if price not in self.bids:
            self.bids[price] = deque()
            heapq.heappush(self.bid_heap, -price)

        self.bids[price].append(order)

     else:
        order.status = "FILLED"

    # 6. Calculate execution report
     average_price = (
        total_value / filled_quantity
        if filled_quantity > 0 else 0
    )

     return {
        "requested_quantity": requested_quantity,
        "filled_quantity": filled_quantity,
        "remaining_quantity": order.quantity,
        "average_execution_price": average_price,
        "order_id": order_id,
        "status": order.status
    }


    def add_limit_sell(self, price, quantity, trader_id):

     requested_quantity = quantity
     filled_quantity = 0
     total_value = 0

    # 1. Create the incoming order before matching
     order = Order(
        self.next_order_id,
        trader_id,
        "SELL",
        price,
        quantity
    )

     order_id = order.order_id
     self.next_order_id += 1

    # Record every submitted order
     self.order_history[order_id] = order

    # 2. Match against the bid book
     while order.quantity > 0 and self.bids:

        best_bid = self.best_bid()

        if best_bid is None or best_bid < price:
            break

        oldest_order = self.bids[best_bid][0]

        # Self-trade prevention
        if oldest_order.trader_id == trader_id:
            print("Self-trade prevention: incoming sell order canceled")

            order.status = "CANCELED"

            average_price = (
                total_value / filled_quantity
                if filled_quantity > 0 else 0
            )

            return {
                "requested_quantity": requested_quantity,
                "filled_quantity": filled_quantity,
                "remaining_quantity": order.quantity,
                "average_execution_price": average_price,
                "order_id": order_id,
                "status": "CANCELED"
            }

        # 3. Execute the trade
        traded_quantity = min(
            order.quantity,
            oldest_order.quantity
        )

        print(f"TRADE: {traded_quantity} @ {best_bid}")

        self.record_trade(
            best_bid,
            traded_quantity,
            oldest_order.trader_id,
            trader_id
        )

        # Update incoming order
        order.quantity -= traded_quantity
        order.filled_quantity += traded_quantity

        # Update resting order
        oldest_order.quantity -= traded_quantity
        oldest_order.filled_quantity += traded_quantity

        filled_quantity += traded_quantity
        total_value += traded_quantity * best_bid

        # Update resting order status
        if oldest_order.quantity == 0:
            oldest_order.status = "FILLED"
        else:
            oldest_order.status = "PARTIALLY_FILLED"

        # 4. Remove fully filled resting orders
        if oldest_order.quantity == 0:

            filled_order = self.bids[best_bid].popleft()

            del self.order_map[filled_order.order_id]

            if not self.bids[best_bid]:
                del self.bids[best_bid]

    # 5. Add remaining quantity to the ask book
     if order.quantity > 0:

        if order.filled_quantity > 0:
            order.status = "PARTIALLY_FILLED"
        else:
            order.status = "RESTING"

        self.order_map[order_id] = order

        if price not in self.asks:
            self.asks[price] = deque()
            heapq.heappush(self.ask_heap, price)

        self.asks[price].append(order)

     else:
        order.status = "FILLED"

    # 6. Execution report
     average_price = (
        total_value / filled_quantity
        if filled_quantity > 0 else 0
    )

     return {
        "requested_quantity": requested_quantity,
        "filled_quantity": filled_quantity,
        "remaining_quantity": order.quantity,
        "average_execution_price": average_price,
        "order_id": order_id,
        "status": order.status
    }

        
    
    

    def market_buy(self, trader_id, quantity):
     requested_quantity = quantity
     filled_quantity = 0
     total_value = 0

     while quantity > 0:

        best_price = self.best_ask()

        if best_price is None:
            break

        best_ask_order = self.asks[best_price][0]

        # Prevent self-trading
        if best_ask_order.trader_id == trader_id:
            break

        traded_quantity = min(quantity, best_ask_order.quantity)
        execution_price = best_ask_order.price

        # Update quantities
        # Update quantities
        best_ask_order.quantity -= traded_quantity
        best_ask_order.filled_quantity += traded_quantity
        quantity -= traded_quantity

        if best_ask_order.quantity == 0:
         best_ask_order.status = "FILLED"
        else:
         best_ask_order.status = "PARTIALLY_FILLED"

        # Record execution
        self.record_trade(
            execution_price,
            traded_quantity,
            trader_id,
            best_ask_order.trader_id
        )

        filled_quantity += traded_quantity
        total_value += traded_quantity * execution_price

        # Remove completely filled order
        if best_ask_order.quantity == 0:
            self.asks[best_price].popleft()
            del self.order_map[best_ask_order.order_id]

            if not self.asks[best_price]:
                del self.asks[best_price]

     unfilled_quantity = requested_quantity - filled_quantity

     average_price = (
        total_value / filled_quantity
        if filled_quantity > 0 else 0
      )

     return {
        "requested_quantity": requested_quantity,
        "filled_quantity": filled_quantity,
        "unfilled_quantity": unfilled_quantity,
        "average_execution_price": average_price
     }



    def market_sell(self, trader_id, quantity):
     requested_quantity = quantity
     filled_quantity = 0
     total_value = 0

     while quantity > 0:
        best_price = self.best_bid()

        if best_price is None:
            break

        best_bid_order = self.bids[best_price][0]

        # Prevent self-trading
        if best_bid_order.trader_id == trader_id:
            break

        traded_quantity = min(quantity, best_bid_order.quantity)
        execution_price = best_bid_order.price

        # Update quantities
        best_bid_order.quantity -= traded_quantity
        best_bid_order.filled_quantity += traded_quantity
        quantity -= traded_quantity

        if best_bid_order.quantity == 0:
            best_bid_order.status = "FILLED"
        else:
            best_bid_order.status = "PARTIALLY_FILLED"

        # Record execution
        self.record_trade(
            execution_price,
            traded_quantity,
            best_bid_order.trader_id,
            trader_id
        )

        filled_quantity += traded_quantity
        total_value += traded_quantity * execution_price

        # Remove completely filled order
        if best_bid_order.quantity == 0:
            self.bids[best_price].popleft()
            del self.order_map[best_bid_order.order_id]

            if not self.bids[best_price]:
                del self.bids[best_price]

     unfilled_quantity = requested_quantity - filled_quantity

     average_price = (
        total_value / filled_quantity
        if filled_quantity > 0 else 0
    )

     return {
        "requested_quantity": requested_quantity,
        "filled_quantity": filled_quantity,
        "unfilled_quantity": unfilled_quantity,
        "average_execution_price": average_price
    }


    def cancel_order(self, order_id, trader_id):
     order = self.order_map.get(order_id)

     if order is None:
        return False

    # Check ownership
     if order.trader_id != trader_id:
        return False

    # Remove order from the order book
     book_side = self.bids if order.side == "BUY" else self.asks

     if order.price in book_side:
        book_side[order.price].remove(order)

        if not book_side[order.price]:
            del book_side[order.price]

     order.status = "CANCELED"
     del self.order_map[order_id]

     return True

    def record_trade(self, price, quantity, buyer_id, seller_id):

     self.trade_history.append({
        "price": price,
        "quantity": quantity,
        "buyer": buyer_id,
        "seller": seller_id
    })

     buyer = self.traders.get(buyer_id)
     seller = self.traders.get(seller_id)

     if buyer is not None:

        if isinstance(buyer, MarketMaker):
            self.apply_fill(buyer, quantity, price)

        elif hasattr(buyer, "inventory"):
            buyer.inventory += quantity

        if hasattr(buyer, "cash"):
            buyer.cash -= price * quantity

     if seller is not None:

        if isinstance(seller, MarketMaker):
            self.apply_fill(seller, -quantity, price)

        elif hasattr(seller, "inventory"):
            seller.inventory -= quantity

        if hasattr(seller, "cash"):
            seller.cash += price * quantity

    def apply_fill(self, mm, signed_qty, price):
     old_inv = mm.inventory
     new_inv = old_inv + signed_qty

    # Same direction: increase existing position
     if old_inv == 0 or (old_inv > 0) == (signed_qty > 0):
        total_cost = (
            mm.avg_cost * abs(old_inv)
            + price * abs(signed_qty)
        )

        mm.avg_cost = (
            total_cost / abs(new_inv)
            if new_inv != 0 else 0
        )

    # Opposite direction: close existing position
     else:
        closing_qty = min(abs(old_inv), abs(signed_qty))

        mm.realized_pnl += (
            (price - mm.avg_cost)
            * closing_qty
            * (1 if old_inv > 0 else -1)
        )

        remaining = abs(signed_qty) - closing_qty

        if remaining > 0:
            # Position reversed: new position starts at execution price
            mm.avg_cost = price
        elif new_inv == 0:
            mm.avg_cost = 0

     mm.inventory = new_inv

                      
    def best_bid(self):
        while self.bid_heap:
            price = -self.bid_heap[0]
            if price in self.bids:
                return price
            heapq.heappop(self.bid_heap)
        return None

    def best_ask(self):
        while self.ask_heap:
            price = self.ask_heap[0]
            if price in self.asks:
                return price
            heapq.heappop(self.ask_heap)
        return None
    
    def best_bid_excluding(self, trader_id):
     prices = [
        price
        for price, orders in self.bids.items()
        if any(order.trader_id != trader_id for order in orders)
    ]

     return max(prices) if prices else None


    def best_ask_excluding(self, trader_id):
     prices = [
        price
        for price, orders in self.asks.items()
        if any(order.trader_id != trader_id for order in orders)
    ]

     return min(prices) if prices else None
    
    def mid_price(self):
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        if best_bid is not None and best_ask is not None:
            return (best_bid + best_ask)/2
        return None

    def spread(self):
        if not self.bids or not self.asks:
            return None
        return self.best_ask() - self.best_bid()

    def estimate_sigma(self):
        if len(self.trade_history) < 2:
            return 0.02
        prices = [trade["price"] for trade in self.trade_history[-20:]]
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i]-prices[i-1])/prices[i-1])
        if not returns:
            return 0.02    
        mean = sum(returns)/len(returns)
        variance = sum((x-mean)**2 for x in returns)/len(returns)
        return variance**0.5
class MarketMaker:
    def __init__(self,trader_id,):
        self.trader_id = trader_id
        self.inventory = 0
        self.cash = 0
        self.buy_order_id = None
        self.sell_order_id = None
        self.realized_pnl = 0
        self.avg_cost = 0
        self.max_inventory = 20

    def unrealized_pnl(self,mid_price):
        if self.inventory == 0:
         return 0
        return self.inventory * (mid_price - self.avg_cost)
    
    def step(self, book):

    # Cancel previous quotes
     if self.buy_order_id is not None:
        book.cancel_order(self.buy_order_id, self.trader_id)

     if self.sell_order_id is not None:
        book.cancel_order(self.sell_order_id, self.trader_id)

     self.buy_order_id = None
     self.sell_order_id = None

    # Get external market prices
     best_bid = book.best_bid_excluding(self.trader_id)
     best_ask = book.best_ask_excluding(self.trader_id)

     if best_bid is not None and best_ask is not None:
        mid = (best_bid + best_ask) / 2
     elif best_bid is not None:
        mid = best_bid
     elif best_ask is not None:
        mid = best_ask
     else:
        mid = 100

    # Calculate reservation price and spread
     gamma = 0.5
     sigma_pct = book.estimate_sigma()
     sigma = sigma_pct * mid
     tau = 1

     skew = self.inventory * gamma * sigma**2 * tau

     max_skew = 0.1 * mid
     skew = max(-max_skew, min(max_skew, skew))

     r = mid - skew
     spread = max(1, sigma)

     buy_price = int(r - spread / 2)
     sell_price = int(r + spread / 2)

    # Prevent crossing external market
     if best_ask is not None:
        buy_price = min(buy_price, best_ask - 1)

     if best_bid is not None:
        sell_price = max(sell_price, best_bid + 1)

    # Enforce inventory limits, including outstanding orders
     buy_capacity = self.max_inventory - self.inventory
     sell_capacity = self.max_inventory + self.inventory

     buy_quantity = min(5, max(0, buy_capacity))
     sell_quantity = min(5, max(0, sell_capacity))

     print("MM placing quotes")

     if buy_quantity > 0:
        buy_report = book.add_limit_buy(
            buy_price, buy_quantity, self.trader_id
        )
        self.buy_order_id = buy_report["order_id"]

     if sell_quantity > 0:
        sell_report = book.add_limit_sell(
            sell_price, sell_quantity, self.trader_id
        )
        self.sell_order_id = sell_report["order_id"]

     print(
        f"Inventory: {self.inventory}",
        f"Cash: {self.cash}",
        f"Bid={buy_price if buy_quantity > 0 else 'OFF'}",
        f"Ask={sell_price if sell_quantity > 0 else 'OFF'}"
    )

def update_market_price(current_price): 
      movement = random.choice([-1, 0, 1])
      return current_price + movement

if __name__ == "__main__":

    book = OrderBook()

    mm = MarketMaker("MM")
    book.traders["MM"] = mm

    # External liquidity providers
    book.add_limit_buy(98, 10, "T1")
    book.add_limit_sell(102, 10, "T2")
    history = []
    external_bid_id = None
    external_ask_id = None

    print("\nStarting market-making simulation\n")
    market_price = 100


    # Initial quotes
    mm.step(book)

    # Simulate 100 trading periods
    for t in range(1, 101):

        print(f"\n========== TIME STEP {t} ==========")
        market_price = update_market_price(market_price)
        print("Reference market price:", market_price)
        # Cancel previous external quotes
        if external_bid_id is not None:
         book.cancel_order(external_bid_id, "T1")

        if external_ask_id is not None:
         book.cancel_order(external_ask_id, "T2")

# Add fresh external quotes around the new market price
        bid_report = book.add_limit_buy(market_price - 2, 10, "T1")
        ask_report = book.add_limit_sell(market_price + 2, 10, "T2")

        external_bid_id = bid_report["order_id"]
        external_ask_id = ask_report["order_id"]

        # Alternate between external buying and selling
        quantity = random.randint(1, 5)

        if random.random() < 0.5:
         print(f"External trader buys {quantity} units")
         report = book.market_buy("T3", quantity)

        else:
         print(f"External trader sells {quantity} units")
         report = book.market_sell("T4", quantity)

        print("Execution:", report)

        # Update market maker quotes
        mm.step(book)

        # Current market state
        
        external_bid = book.best_bid_excluding("MM")
        external_ask = book.best_ask_excluding("MM")

        if external_bid is not None and external_ask is not None:
         mid = (external_bid + external_ask) / 2
        elif external_bid is not None:
         mid = external_bid
        elif external_ask is not None:
         mid = external_ask
        else:
         mid = None

        unrealized = mm.unrealized_pnl(mid) if mid is not None else 0
        total_pnl = mm.realized_pnl + unrealized
        history.append({
    "time": t,
    "inventory": mm.inventory,
    "cash": mm.cash,
    "mid_price": mid,
    "realized_pnl": mm.realized_pnl,
    "unrealized_pnl": unrealized,
    "total_pnl": total_pnl, "reference_price": market_price,
    "inventory": mm.inventory,
})

        print("External Mid:", mid)
        print("Realized P&L:", mm.realized_pnl)
        print("Unrealized P&L:", unrealized)
        print("Total P&L:", total_pnl)


        print("Best bid:", book.best_bid())
        print("Best ask:", book.best_ask())
        print("Inventory:", mm.inventory)
        print("Cash:", mm.cash)
        print("Realized P&L:", mm.realized_pnl)
        print("Unrealized P&L:", mm.unrealized_pnl(mid) if mid else 0)


    print("\n========== SIMULATION SUMMARY ==========")

    print("Final P&L:", history[-1]["total_pnl"])
    print("Maximum inventory:", max(abs(x["inventory"]) for x in history))
    print("Minimum P&L:", min(x["total_pnl"] for x in history))
    print("Maximum P&L:", max(x["total_pnl"] for x in history))

    print("\n========== PRICE AND INVENTORY HISTORY ==========")

    for row in history:
     print(
        "Time:", row["time"],
        "Price:", row["reference_price"],
        "Inventory:", row["inventory"],
        "P&L:", row["total_pnl"]
    )
    
