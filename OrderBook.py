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
                book.cancel_order(order_id)

class Order:
    def __init__(self, order_id, trader_id,side, price, quantity):
        self.order_id = order_id
        self.trader_id = trader_id
        self.side = side
        self.price = price
        self.quantity = quantity


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


    def add_limit_buy(self,price,quantity,trader_id):

        while quantity > 0 and self.asks:
            best_ask = self.best_ask()
            if best_ask is None:
                break
            if best_ask > price:
                break
            oldest_order = self.asks[best_ask][0]
            if oldest_order.trader_id == trader_id:
                break
            available = oldest_order.quantity
            if quantity < available:
                print(f"TRADE: {quantity}@{best_ask}")
                self.record_trade(best_ask,quantity,trader_id,oldest_order.trader_id)
                oldest_order.quantity -= quantity
                quantity = 0
                
            else:
                quantity -= available
                print(f"TRADE: {available} @ {best_ask}")
                self.record_trade(best_ask,available,trader_id,oldest_order.trader_id)
                filled_order = self.asks[best_ask][0]
                del self.order_map[filled_order.order_id]
                self.asks[best_ask].popleft()
                if not self.asks[best_ask]:
                    del self.asks[best_ask]
            

        if quantity > 0:
            order =Order(self.next_order_id,trader_id,"BUY",price,quantity)
            self.order_map[order.order_id] = order
            self.next_order_id +=1
            order_id = order.order_id

            if price not in self.bids:
                self.bids[price] = deque()
                heapq.heappush(self.bid_heap, -price)
            self.bids[price].append(order)

            return order_id
        return None
        
    def add_limit_sell(self,price,quantity,trader_id):
        while quantity > 0 and self.bids:
            best_bid = self.best_bid()
            if best_bid is None:
                break
            if best_bid < price:
                break
            oldest_order = self.bids[best_bid][0]
            if oldest_order.trader_id == trader_id:
                break
            available = oldest_order.quantity
            if quantity < available:
                print(f"TRADE: {quantity}@{best_bid}")
                self.record_trade(best_bid, quantity, oldest_order.trader_id, trader_id)
                oldest_order.quantity -= quantity
                quantity = 0
            else:
                quantity -= available
                print(f"TRADE: {available} @ {best_bid}")
                self.record_trade(best_bid, available, oldest_order.trader_id, trader_id)
                filled_order = self.bids[best_bid][0]
                del self.order_map[filled_order.order_id]
                self.bids[best_bid].popleft()
                if not self.bids[best_bid]:
                    del self.bids[best_bid]

        if quantity > 0:
            order = Order(self.next_order_id,trader_id,"SELL",price,quantity)
            self.order_map[order.order_id] = order
            self.next_order_id +=1
            order_id = order.order_id

            if price not in self.asks:
                self.asks[price] = deque()
                heapq.heappush(self.ask_heap, price)
            self.asks[price].append(order)
            return order_id
        return None

    def print_book(self):
        print("ASKS")
        for price in sorted(self.asks):
            print(price, ";", self.asks[price])

        print()
        print("BIDS")
        for price in sorted(self.bids, reverse = True):
            print(price, ":", self.bids[price])

    def market_buy(self, quantity, trader_id):
        if not self.asks:
            print("No liquidity available")
            return
        best_ask = self.best_ask()
        oldest_order = self.asks[best_ask][0]
        if oldest_order.trader_id == trader_id:
            print("Self trade detected")
            return
        available = oldest_order.quantity
        if quantity <= available:
            self.record_trade(best_ask,quantity,trader_id,oldest_order.trader_id)
            oldest_order.quantity -= quantity
            if oldest_order.quantity == 0:
                filled_order = self.asks[best_ask][0]
                del self.order_map[filled_order.order_id]
                self.asks[best_ask].popleft()
                if not self.asks[best_ask]:
                    del self.asks[best_ask]
        else:
            self.record_trade(best_ask, available, trader_id, oldest_order.trader_id)
            filled_order = self.asks[best_ask][0]
            del self.order_map[filled_order.order_id]
            self.asks[best_ask].popleft()
            if not self.asks[best_ask]:
                del self.asks[best_ask]
            quantity -= available
            self.market_buy(quantity, trader_id)

    def market_sell(self,quantity,trader_id):
        if not self.bids:
            print("No liquidity available")
            return
        best_bid = self.best_bid()
        oldest_order = self.bids[best_bid][0]
        if oldest_order.trader_id == trader_id:
            print("Self trade detected")
            return
        available = oldest_order.quantity
        if quantity <= available:
            self.record_trade(best_bid, quantity, trader_id, oldest_order.trader_id)
            oldest_order.quantity -= quantity
            if oldest_order.quantity == 0:
                 filled_order = self.bids[best_bid][0]
                 del self.order_map[filled_order.order_id]
                 self.bids[best_bid].popleft()
                 if not self.bids[best_bid]:
                     del self.bids[best_bid]
        else:
            self.record_trade(best_bid, available, trader_id, oldest_order.trader_id)
            filled_order = self.bids[best_bid][0]
            del self.order_map[filled_order.order_id]
            self.bids[best_bid].popleft()
            if not self.bids[best_bid]:
                del self.bids[best_bid]
            quantity -= available 
            self.market_sell(quantity, trader_id)

    def cancel_order(self, order_id):

     order = self.order_map.get(order_id)

     if order is None:
        return
     
     price = order.price

     if order.side == "BUY":

        self.bids[price].remove(order)

        if not self.bids[price]:
            del self.bids[price]

     else:

        self.asks[price].remove(order)

        if not self.asks[price]:
            del self.asks[price]

     del self.order_map[order_id]

    def record_trade(self, price, quantity, buyer_id, seller_id):
        self.trade_history.append({"price":price, "quantity":quantity, "buyer":buyer_id, "seller":seller_id})
        buyer = self.traders.get(buyer_id)
        seller = self.traders.get(seller_id)
        if buyer is not None:
            if isinstance(buyer, MarketMaker):
                self.apply_fill(buyer,quantity,price)
            if hasattr(buyer, "cash"):
                buyer.cash -= price*quantity
            if hasattr(buyer, "inventory"):
                buyer.inventory += quantity


            
        if seller is not None:
            if isinstance(seller, MarketMaker):
                self.apply_fill(seller,-quantity,price)
            if hasattr(seller, "cash"):
                seller.cash+= price*quantity
            if hasattr(seller, "inventory"):
                seller.inventory -= quantity


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
            book.cancel_order(self.buy_order_id)
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
market_maker = MarketMaker("MM")
traders = [RandomTrader("T1"), RandomTrader("T2"), RandomTrader("T3"), RandomTrader("T4"), market_maker]
book.traders["MM"] = market_maker
for trader in traders:
    book.traders[trader.trader_id] = trader
inventory_history = []
cash_history = []
pnl_history = []
for _ in range(100):
    trader = random.choice(traders)
    if trader.trader_id == "MM":
        print("MM selected")
    trader.step(book)

    inventory_history.append(market_maker.inventory)
    cash_history.append(market_maker.cash)
    pnl_history.append(market_maker.cash + market_maker.inventory * (book.mid_price() if book.mid_price() is not None else 100))


print(book.trade_history[:10])

inventory = {"T1":0, "T2" :0, "T3":0, "T4":0, "MM":0}
cash = {"T1":0, "T2":0, "T3":0, "T4":0, "MM":0}
for trade in book.trade_history:
    if trade["buyer"] == trade["seller"]:
        print(trade)

    inventory[trade["buyer"]] += trade["quantity"]
    inventory[trade["seller"]] -= trade["quantity"]
    cash[trade["buyer"]] -= trade["price"] * trade["quantity"]
    cash[trade["seller"]] += trade["price"] * trade["quantity"]
    inventory_history.append(market_maker.inventory)
    cash_history.append(market_maker.cash)
print(inventory)
print(cash)
print(inventory_history)
print(cash_history)
print(pnl_history)  
mid = book.mid_price()
pnl = {}
if mid is None:
    mid = 100
else:
    for trader in inventory:
        pnl[trader] = cash[trader] + inventory[trader] * mid
    print(pnl)

print("Final Inventory =", market_maker.inventory)
print("Final Cash =", market_maker.cash)
print("Final Unrealized PnL =", market_maker.unrealized_pnl(mid))
print("Final Realized PnL =", market_maker.realized_pnl)

print(
    "Total PnL =",
    market_maker.realized_pnl +
    market_maker.unrealized_pnl(mid)
)

