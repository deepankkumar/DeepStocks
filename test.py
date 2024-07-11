# get the news for the selected stock
import yahooquery as yf

def get_news(Ticker):
    stock = yf.Ticker(Ticker)
    news = stock.news()
    return news

# get the financials for the selected stock
ticker = "AAPL"

# get the news for the selected stock
stock = yf.Ticker(ticker)

print(stock.news())