import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
df = pd.read_csv('prices_round_0_day_-1.csv', sep = ';')
print(df.head())
tomatoes = df[df["product"] == "TOMATOES"]
print(tomatoes[["timestamp", "mid_price"]].head(20))
plt.plot(tomatoes["timestamp"], tomatoes["mid_price"])
plt.show()
prices = []
ma_values = []
buy_points = []
sell_points = []
window_size = 20
history = []
prev_mid = None
prev_ma = None
position = 0
cooldown = 0
cooldown_period = 50
for index, row in tomatoes.iterrows():
    mid_price = row["mid_price"]
    history.append(mid_price)
    prices.append(mid_price)

    if cooldown > 0:
        cooldown -= 1

    if len(history) >= window_size:
        ma = sum(history[-window_size:])/window_size
        ma_values.append(ma)
        if prev_mid is not None and cooldown == 0:
            if prev_mid <= prev_ma and mid_price > ma and position <= 0:
                buy_points.append((index, mid_price))
                position = 1
                cooldown = cooldown_period
            elif prev_mid >= prev_ma and mid_price < ma and position >=0:
                sell_points.append((index, mid_price))
                position = -1
                cooldown = cooldown_period
        prev_mid = mid_price
        prev_ma = ma
    else:
        ma_values.append(None)

plt.plot(prices , label = 'Price')
plt.plot(ma_values, label = 'Moving Average')
for i,price in buy_points:
    plt.scatter(i,price)
for i,price in sell_points:
    plt.scatter(i,price)
plt.legend()
plt.show()

        


    