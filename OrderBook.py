import random
import heapq
from collections import deque
import matplotlib.pyplot as plt


class RandomTrader:
    def __init__(self, trader_id):
        self.trader_id = trader_id

    def step(self, book):
        action = random.choice(["limit_buy","limit_sell","market_buy","market_sell"])
        price = random.randint(95,105)
        quantity = random.randint(1,10)

        if action == "limit_buy":
            book.add_limit_buy(price,quantity,self.trader_id)

        elif action == "limit_sell":
            book.add_limit_sell(price,quantity, self.trader_id)

        elif action == "market_buy":
            book.market_buy(quantity, self.trader_id)

        elif action == "market_sell":
            book.market_sell(quantity, self.trader_id)

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
                self.trade_history.append({"price" : best_ask, "quantity" : quantity, "buyer" : trader_id, "seller" : oldest_order.trader_id})
                oldest_order.quantity -= quantity
                quantity = 0
                
            else:
                quantity -= available
                print(f"TRADE: {available} @ {best_ask}")
                self.trade_history.append({"price" : best_ask, "quantity" : available, "buyer" : trader_id, "seller" : oldest_order.trader_id})
                self.asks[best_ask].popleft()
                if not self.asks[best_ask]:
                    del self.asks[best_ask]
            

        if quantity > 0:
            order =Order(self.next_order_id,trader_id,"BUY",price,quantity)
            self.next_order_id +=1

            if price not in self.bids:
                self.bids[price] = deque()
                heapq.heappush(self.bid_heap, -price)
            self.bids[price].append(order)

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
                self.trade_history.append({"price" : best_bid, "quantity" : quantity, "buyer" : oldest_order.trader_id, "seller" : trader_id})
                oldest_order.quantity -= quantity
                quantity = 0
            else:
                quantity -= available
                print(f"TRADE: {available} @ {best_bid}")
                self.trade_history.append({"price" : best_bid, "quantity" : available, "buyer" : oldest_order.trader_id, "seller" : trader_id})
                self.bids[best_bid].popleft()
                if not self.bids[best_bid]:
                    del self.bids[best_bid]

        if quantity > 0:
            order = Order(self.next_order_id,trader_id,"SELL",price,quantity)
            self.next_order_id +=1

            if price not in self.asks:
                self.asks[price] = deque()
                heapq.heappush(self.ask_heap, price)
            self.asks[price].append(order)

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
            self.trade_history.append({"price" : best_ask, "quantity" : quantity, "buyer" : trader_id, "seller" : oldest_order.trader_id})
            oldest_order.quantity -= quantity
            if oldest_order.quantity == 0:
                self.asks[best_ask].popleft()
                if not self.asks[best_ask]:
                    del self.asks[best_ask]
        else:
            self.trade_history.append({"price":best_ask, "quantity" : available, "buyer" : trader_id, "seller" : oldest_order.trader_id})
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
            self.trade_history.append({"price": best_bid, "quantity" : quantity, "buyer" : oldest_order.trader_id, "seller" : trader_id})
            oldest_order.quantity -= quantity
            if oldest_order.quantity == 0:
                 self.bids[best_bid].popleft()
                 if not self.bids[best_bid]:
                     del self.bids[best_bid]
        else:
            self.trade_history.append({"price" : best_bid, "quantity": available, "buyer" : oldest_order.trader_id, "seller" : trader_id})
            self.bids[best_bid].popleft()
            if not self.bids[best_bid]:
                del self.bids[best_bid]
            quantity -= available 
            self.market_sell(quantity, trader_id)

    def cancel_order(self, order_id):
        for price in self.bids:
            for order in self.bids[price]:
                if order.order_id == order_id:
                    self.bids[price].remove(order)
                    if not self.bids[price]:
                        del self.bids[price]
                        return
        
        for price in self.asks:
            for order in self.asks[price]:
                if order.order_id == order_id:
                    self.asks[price].remove(order)
                    if not self.asks[price]:
                        del self.asks[price]
                        return
                    
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
    
class MarketMaker:
    def __init__(self,trader_id):
        self.trader_id = trader_id
        self.inventory = 0
        self.cash = 0


    def step(self,book):
        mid = book.mid_price()
        if mid is None:
            mid=100
        gamma = 0.01
        sigma = 2
        tau = 1
        r = mid - self.inventory*gamma*sigma**2*tau
        spread = 2
        buy_price = int(r - spread/2)
        sell_price = int(r + spread/2)
        print("MM placing quotes")
        book.add_limit_buy(buy_price, 5, self.trader_id)
        book.add_limit_sell(sell_price, 5, self.trader_id)
        print(f"Inventory: {self.inventory}", f"Cash: {self.cash}", f"Bid={buy_price:.2f}, "
    f"Ask={sell_price:.2f}")


    

book = OrderBook()
market_maker = MarketMaker("MM")
traders = [RandomTrader("T1"), RandomTrader("T2"), RandomTrader("T3"), RandomTrader("T4"), market_maker]
inventory_history = []
cash_history = []
pnl_history = []
for _ in range(100):
    trader = random.choice(traders)
    if trader.trader_id == "MM":
        print("MM selected")
    trader.step(book)
    mm_inventory = 0
    for trade in book.trade_history:
        if trade["buyer"] == "MM":
            mm_inventory += trade["quantity"]
        if trade["seller"] == "MM":
            mm_inventory -= trade["quantity"]
    market_maker.inventory = mm_inventory
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
    print("No mid price available")
else:
    for trader in inventory:
        pnl[trader] = cash[trader] + inventory[trader] * mid
    print(pnl)

