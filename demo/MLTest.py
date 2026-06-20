import requests

ticker = 'AAPL'
url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&ticker={ticker}&apikey=DMZ57B8EW0H0LZJ&limit=10'
r = requests.get(url)
data = r.json()

print(data)

# prediction if BUY, SELL or HOLD
print("\n📈 Stock Performance Prediction:")
cluster_action_map = {
    0: "BUY",
    1: "HOLD",
    2: "SELL"
}
if cluster_action_map == 0:
    print(f"it is recommended to BUY {ticker}")
elif cluster_action_map == 1:
    print(f"it is recommended to HOLD {ticker}")
else:
    print(f"it is recommended to SELL {ticker}")
