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

    
    def add_limit_buy(self, price, quantity, trader_id):

     requested_quantity = quantity
     filled_quantity = 0
     incoming_filled = 0
     total_value = 0
     order_id = None

     while quantity > 0 and self.asks:

        best_ask = self.best_ask()

        if best_ask is None or best_ask > price:
            break

        oldest_order = self.asks[best_ask][0]

        # Self-trade prevention
        if oldest_order.trader_id == trader_id:
            print("Self-trade prevention: incoming buy order rejected")

            return {
                "requested_quantity": requested_quantity,
                "filled_quantity": filled_quantity,
                "remaining_quantity": quantity,
                "average_execution_price": (
                    total_value / filled_quantity
                    if filled_quantity > 0 else 0
                ),
                "order_id": None,
                "status": "REJECTED"
            }

        available = oldest_order.quantity
        traded_quantity = min(quantity, available)

        print(f"TRADE: {traded_quantity} @ {best_ask}")

        self.record_trade(
            best_ask,
            traded_quantity,
            trader_id,
            oldest_order.trader_id
        )

        oldest_order.quantity -= traded_quantity
        oldest_order.filled_quantity += traded_quantity
        quantity -= traded_quantity

        if oldest_order.quantity == 0:
          oldest_order.status = "FILLED"
        else:
          oldest_order.status = "PARTIALLY_FILLED"

        filled_quantity += traded_quantity
        incoming_filled += traded_quantity
        total_value += traded_quantity * best_ask

        if oldest_order.quantity == 0:

            filled_order = self.asks[best_ask].popleft()
            del self.order_map[filled_order.order_id]

            if not self.asks[best_ask]:
                del self.asks[best_ask]

    # Add remaining quantity to the order book
     if quantity > 0:

        order = Order(
            self.next_order_id,
            trader_id,
            "BUY",
            price,
            quantity
        )
        order.filled_quantity = incoming_filled

        order.status = ("PARTIALLY_FILLED" if incoming_filled > 0 else "RESTING")

        order_id = order.order_id
        self.order_map[order_id] = order
        self.order_history[order.order_id] = order
        self.next_order_id += 1

        if price not in self.bids:
            self.bids[price] = deque()
            heapq.heappush(self.bid_heap, -price)

        self.bids[price].append(order)

     average_price = (
        total_value / filled_quantity
        if filled_quantity > 0 else 0
     )

     if filled_quantity == 0:
        status = "RESTING"
     elif quantity == 0:
        status = "FILLED"
     else:
        status = "PARTIALLY_FILLED"

     return {
        "requested_quantity": requested_quantity,
        "filled_quantity": filled_quantity,
        "remaining_quantity": quantity,
        "average_execution_price": average_price,
        "order_id": order_id,
        "status": status
    }

        
    
    def add_limit_sell(self, price, quantity, trader_id):

     requested_quantity = quantity
     filled_quantity = 0
     incoming_filled = 0
     total_value = 0
     order_id = None

     while quantity > 0 and self.bids:

        best_bid = self.best_bid()

        if best_bid is None or best_bid < price:
            break

        oldest_order = self.bids[best_bid][0]

        # Self-trade prevention
        if oldest_order.trader_id == trader_id:
            print("Self-trade prevention: incoming sell order rejected")

            return {
                "requested_quantity": requested_quantity,
                "filled_quantity": filled_quantity,
                "remaining_quantity": quantity,
                "average_execution_price": (
                    total_value / filled_quantity
                    if filled_quantity > 0 else 0
                ),
                "order_id": None,
                "status": "REJECTED"
            }

        available = oldest_order.quantity
        traded_quantity = min(quantity, available)

        print(f"TRADE: {traded_quantity} @ {best_bid}")

        self.record_trade(
            best_bid,
            traded_quantity,
            oldest_order.trader_id,
            trader_id
        )

        oldest_order.quantity -= traded_quantity
        oldest_order.filled_quantity += traded_quantity
        quantity -= traded_quantity

        if oldest_order.quantity == 0:
         oldest_order.status = "FILLED"
        else:
         oldest_order.status = "PARTIALLY_FILLED"

        filled_quantity += traded_quantity
        incoming_filled += traded_quantity
        total_value += traded_quantity * best_bid

        if oldest_order.quantity == 0:

            filled_order = self.bids[best_bid].popleft()
            del self.order_map[filled_order.order_id]

            if not self.bids[best_bid]:
                del self.bids[best_bid]

    # Add remaining quantity to the order book
     if quantity > 0:

        order = Order(
            self.next_order_id,
            trader_id,
            "SELL",
            price,
            quantity
        )
        order.filled_quantity = incoming_filled
        order.status = ("PARTIALLY_FILLED" if incoming_filled > 0 else "RESTING")
        

        order_id = order.order_id
        self.order_map[order_id] = order
        self.order_history[order_id] = order
        self.next_order_id += 1

        if price not in self.asks:
            self.asks[price] = deque()
            heapq.heappush(self.ask_heap, price)

        self.asks[price].append(order)

     average_price = (
        total_value / filled_quantity
        if filled_quantity > 0 else 0
     )

     if filled_quantity == 0:
        status = "RESTING"
     elif quantity == 0:
        status = "FILLED"
     else:
        status = "PARTIALLY_FILLED"

     return {
        "requested_quantity": requested_quantity,
        "filled_quantity": filled_quantity,
        "remaining_quantity": quantity,
        "average_execution_price": average_price,
        "order_id": order_id,
        "status": status
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
        best_ask_order.quantity -= traded_quantity
        quantity -= traded_quantity

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
        quantity -= traded_quantity

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
     book_side = self.bids if order.side == "buy" else self.asks

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

    def apply_fill(self,mm,signed_qty,price):
        old_inv = mm.inventory 
        new_inv = old_inv + signed_qty
        if old_inv == 0 or (old_inv > 0 ) == (signed_qty > 0):
            total_cost = mm.avg_cost * abs(old_inv) + price * abs(signed_qty)
            mm.avg_cost = total_cost/abs(new_inv) if new_inv != 0 else 0
        else:
            closing_qty =  min(abs(old_inv), abs(signed_qty))       
            mm.realized_pnl += (price - mm.avg_cost) * closing_qty * (1 if old_inv > 0 else -1)
            remaining = abs(signed_qty) - closing_qty
            if remaining > 0:
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

    def unrealized_pnl(self,mid_price):
        if self.inventory == 0:
         return 0
        return self.inventory * (mid_price - self.avg_cost)


    def step(self,book):
        if self.buy_order_id is not None:
            book.cancel_order(self.trader_id, self.buy_order_id)
        if self.sell_order_id is not None:
            book.cancel_order(self.sell_order_id)

        mid = book.mid_price()
        if mid is None:
            mid=100
        gamma = 0.5
        sigma_pct = book.estimate_sigma()
        sigma = sigma_pct * mid
        tau = 1
        skew = self.inventory*gamma*sigma**2*tau
        max_skew = 0.1 * mid
        skew = max(-max_skew, min(max_skew,skew))
        r = mid - skew
        spread = max(1, sigma)
        buy_price = int(r - spread/2)
        sell_price = int(r + spread/2)
        print("MM placing quotes")
        self.buy_order_id = book.add_limit_buy(buy_price, 5, self.trader_id)
        self.sell_order_id = book.add_limit_sell(sell_price, 5, self.trader_id)
        print(f"Inventory: {self.inventory}", f"Cash: {self.cash}", f"Bid={buy_price:.2f}, "
    f"Ask={sell_price:.2f}")


    


    
book = OrderBook()

# T1 offers 3 units at 100
book.add_limit_sell(100, 3, "T1")

# T2 wants to buy 5 units at 105
report = book.add_limit_buy(105, 5, "T2")

print("Execution report:", report)

# Find T2's resting order
order_id = report["order_id"]

order = book.order_map[order_id]

print("Before cancellation:")
print("Filled:", order.filled_quantity)
print("Remaining:", order.quantity)
print("Status:", order.status)

# Cancel T2's remaining order
book.cancel_order(order_id, "T2")

print("After cancellation:")
print("Status:", order.status)
print(book.order_map)
print(book.order_history[order_id].status)