import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import itertools
import statsmodels.api as sm
import matplotlib.pyplot as plt
import warnings

# 1. Mute warnings
warnings.filterwarnings("ignore")

# 2. Define Tickers
tickers = ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"]

print("Starting data download...")

try:
    # 3. Download - auto_adjust=True handles the 'Adj Close' vs 'Close' issue
    raw_data = yf.download(tickers, start="2022-01-01", end="2026-01-01", auto_adjust=True)
    
    # 4. In newer yfinance versions, 'Close' is the adjusted price if auto_adjust=True
    if 'Close' in raw_data.columns:
        data = raw_data['Close']
    elif 'Adj Close' in raw_data.columns:
        data = raw_data['Adj Close']
    else:
        # If all else fails, just take the raw data
        data = raw_data
        
    if data.empty:
        print("Error: DataFrame is empty.")
    else:
        # 5. Drop any missing values (important for NIFTY stocks with different holidays)
        data = data.dropna()
        print("\n--- Success! ---")
        print(f"Data Shape: {data.shape}")
        print("First 5 rows of price data:")
        print(data.head())

except Exception as e:
    print(f"An unexpected error occurred: {e}")
    # This helps us debug if it fails again
    print("Available columns were:", raw_data.columns if 'raw_data' in locals() else "None")

def find_cointegrated_pairs(df):
    n = df.shape[1]
    score_matrix = np.zeros((n,n))
    pvalue_matrix = np.ones((n,n))
    keys = df.columns
    pairs = []

    for i,j in itertools.combinations(range(n),2):
        stock1 = df[keys[i]]
        stock2 = df[keys[j]]
        result = coint(stock1,stock2)
        pvalue = result[1]
        if pvalue < 0.10:
            pairs.append((keys[i], keys[j], pvalue))

    return pairs

print("\nScanning for cointegrated pairs...")
found_pairs = find_cointegrated_pairs(data)

if not found_pairs:
    print("No pairs found with p-value < 0.10. Try increasing the date range or tickers.")
else:
    for p in found_pairs:
        print(f"Pair: {p[0]} and {p[1]} | P-Value: {p[2]:.4f}")


S1_ticker = "RELIANCE.NS"
S2_ticker = "SBIN.NS"

S1 = data[S1_ticker]
S2 = data[S2_ticker]


S1_with_const = sm.add_constant(S1)
model = sm.OLS(S2, S1_with_const).fit()
hedge_ratio = model.params[S1_ticker]
intercept = model.params['const']

spread = S2 - (hedge_ratio * S1 + intercept)

window = 30
spread_mean = spread.rolling(window=window).mean()
spread_std = spread.rolling(window=window).std()
z_score = (spread - spread_mean)/spread_std

print(f"Hedge Ratio (Beta) : {hedge_ratio:.4f}")
print(f"Current Z-Score: {z_score.iloc[-1]:.4f}")

plt.figure(figsize=(14,7))
z_score.plot()
plt.axhline(0, color='black')
plt.axhline(2.0, color = 'red', linestyle='--')
plt.axhline(-2.0, color = 'green', linestyle='--')
plt.title(f"Z-Score spread : {S1_ticker} vs {S2_ticker}")
plt.show()

df_trade = pd.DataFrame(index = z_score.index)
df_trade['z'] = z_score
df_trade['position'] = 0

df_trade.loc[df_trade['z'] < -2.0, 'position'] = 1
df_trade.loc[df_trade['z'] > 2.0, 'position'] = -1

df_trade['position'] = df_trade['position'].ffill().fillna(0)

ret_S1 = S1.pct_change()
ret_S2 = S2.pct_change()
df_trade['strat_ret'] = df_trade['position'].shift(1) * (ret_S2 - hedge_ratio * ret_S1)

costs = 0.001
df_trade['trades'] = df_trade['position'].diff().abs()
df_trade['net_rate'] = df_trade['strat_ret'] - (df_trade['trades'] * costs)

cum_ret = (1 + df_trade['net_rate'].fillna(0)).cumprod()
sharpe = (df_trade['net_rate'].mean() / df_trade['net_rate'].std()) * np.sqrt(252)

print(f"\n--- Final Performance Metrics ---")
print(f"Total Cumulative Return: {(cum_ret.iloc[-1]-1)*100:.2f}%")
print(f"Annualized Sharpe Ratio: {sharpe:.2f}")

plt.figure(figsize=(12,6))
plt.plot(cum_ret, color='blue', label='Strategy Returns (Net of Costs)')
plt.title(f"Cumulative Profit: {S1_ticker} vs {S2_ticker}")
plt.xlabel("Date")
plt.ylabel("Growth of 1 Rupee")
plt.legend()
plt.show()