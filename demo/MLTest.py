import yfinance as yf
import pandas as pd
import requests

ticker = 'NVDA'

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&ticker={ticker}&apikey=DMZ57B8EW0H0LZJ&limit=10'
r = requests.get(url)
data = r.json()

print(data)