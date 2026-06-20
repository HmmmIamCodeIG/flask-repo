import requests

ticker = 'AAPL'
url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&ticker={ticker}&apikey=DMZ57B8EW0H0LZJ&limit=10'
r = requests.get(url)
data = r.json()

print(data)