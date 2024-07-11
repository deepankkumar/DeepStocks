import yfinance as yf
from yahooquery import Ticker
import pandas as pd

def get_stock_info(Ticker, after_hours=False):
    stock = yf.Ticker(Ticker)
    try:
        info = {
            "name": stock.info['longName'],
            "sector": stock.info.get('sector', 'N/A'),
            "currentPrice": stock.info.get('currentPrice', 'N/A'),
            "summary": stock.info.get('longBusinessSummary', 'No summary available.')
        }
        stock.info["sector"] = stock.info.get('sector', 'N/A')
        stock.info["currentPrice"] = stock.info.get('currentPrice', 'N/A')
        stock.info["longBusinessSummary"] = stock.info.get('longBusinessSummary', 'No summary available.')
        try:
            stock.info["currentPrice"] = stock.history(period='1d', interval="1m", auto_adjust=False, prepost = after_hours)['Close'].iloc[-1]
        except:
            stock.info["currentPrice"] = stock.history(period='1d', interval="1m", auto_adjust=False)['Close'].iloc[-1]
        return stock.info
    except KeyError:
        return None

def get_historical_data(ticker, period="1y"):
    period_dict = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "YTD": "YTD", "1Y": "1y", "2Y": "2y", "5Y": "5y", "MAX": "max"}
    period = period_dict[period]
    stock = yf.Ticker(ticker)
    interval = "1d" if period in ["5d", "1mo", "3mo", "6mo", "1y", "YTD"] else "15m" if period == "1d" else "1wk" if period in ["2y", "5y"] else "1mo"
    historical_data = stock.history(period=period, interval=interval, auto_adjust=False)
    historical_data['Adj Close'] = historical_data['Close']
    if 'Adj Close' not in historical_data.columns:
        historical_data['Adj Close'] = historical_data['Close']
    historical_data.index = historical_data.index.tz_localize(None)
    return historical_data

def calculate_portfolio_value(username, portfolio_name, interval, load_csv, get_historical_data):
    df = load_csv(username, portfolio_name)
    tickers = df["Ticker"].unique().tolist()
    
    portfolio_value = pd.DataFrame()
    for ticker in tickers:
        historical_data = get_historical_data(ticker, period=interval)
        shares = df.loc[df['Ticker'] == ticker, 'Shares'].sum()
        historical_data['Value'] = historical_data['Adj Close'] * shares
        if portfolio_value.empty:
            portfolio_value = historical_data[['Value']].rename(columns={'Value': ticker})
        else:
            portfolio_value[ticker] = historical_data['Value']
    
    portfolio_value['Total Portfolio Value'] = portfolio_value.sum(axis=1)
    return portfolio_value

def calculate_sp500_comparison(initial_investment, interval, get_historical_data):
    sp500_data = get_historical_data("^GSPC", period=interval)
    sp500_initial_price = sp500_data['Adj Close'].iloc[0]
    sp500_data['Investment Value'] = (initial_investment / sp500_initial_price) * sp500_data['Adj Close']
    return sp500_data

def get_etf_sector_weightings(ticker):
    stock = Ticker(ticker)
    sector_weightings = stock.fund_holding_info.get(ticker, {}).get('sectorWeightings', [])
    return sector_weightings

def get_analyst_recommendations(ticker):
    stock = Ticker(ticker)
    recommendations = stock.recommendation_trend
    if recommendations is not None and not recommendations.empty:
        latest_period = recommendations.loc[ticker].iloc[-1]
        merged_recommendations = pd.Series({
            'Buy': latest_period['strongBuy'] + latest_period['buy'],
            'Hold': latest_period['hold'],
            'Sell': latest_period['strongSell'] + latest_period['sell']
        })
        return merged_recommendations
    return None

def calculate_recommendation_percentages(recommendations):
    total_recommendations = recommendations.sum()
    percentages = recommendations / total_recommendations * 100
    return percentages
