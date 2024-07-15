import json
import os
import pandas as pd

def load_portfolios(username):
    try:
        with open(f'db/{username}_portfolios.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_portfolios(username, portfolios):
    with open(f'db/{username}_portfolios.json', 'w') as f:
        json.dump(portfolios, f)

def save_csv(username, portfolio_name, df):
    os.makedirs(f'assets/{username}', exist_ok=True)
    df.to_csv(f'assets/{username}/{portfolio_name}.csv', index=False)

def load_csv(username, portfolio_name):
    return pd.read_csv(f'assets/{username}/{portfolio_name}.csv')

def refresh_portfolio(username, portfolio_name, stocks, get_stock_info, after_hours=False):
    updated_stocks = []
    for stock in stocks:
        Ticker = stock["Ticker"]
        Shares = float(stock["Shares"])
        Buy_rate = float(stock["Buy rate ($/unit)"])
        # save the date with datetime object
        Buy_date = stock["Buy date"]
        
        stock_info = get_stock_info(Ticker, after_hours=after_hours)
        if stock_info:
            current_price = stock_info["currentPrice"]
            if current_price == 'N/A':
                current_price = stock_info["previousClose"]
            current_price = float(current_price)
            cost_basis = Shares * Buy_rate
            current_value = Shares * current_price
            profit = current_value - cost_basis
            profit_percentage = (profit / cost_basis) * 100
            # Calculate today's gain
            previous_close = stock_info["previousClose"]
            today_gain = (current_price - previous_close) * Shares
            today_gain_percentage = ((current_price - previous_close) / previous_close) * 100
            
            updated_stocks.append({
                "Ticker": Ticker,
                "Name": stock_info["shortName"],
                "Type": stock_info["quoteType"],
                "Shares": Shares,
                "Buy date": Buy_date,
                "Buy rate ($/unit)": Buy_rate,
                "Current rate ($/unit)": current_price,
                "Cost basis": cost_basis,
                "Current value": current_value,
                "Total profit": profit,
                "Total profit (%)": profit_percentage,
                "Today Gain": today_gain,
                "Today Gain (%)": today_gain_percentage
            })
    df = pd.DataFrame(updated_stocks)
    save_csv(username, portfolio_name, df)
    return df

def merge_stocks(df):
    grouped_df = df.groupby("Ticker").agg({
        "Name": "first",
        "Type": "first",
        "Shares": "sum",
        "Buy rate ($/unit)": lambda x: (df.loc[x.index, "Shares"] * x).sum() / df.loc[x.index, "Shares"].sum(),
        "Current rate ($/unit)": "first",
        "Cost basis": "sum",
        "Current value": "sum",
        "Total profit": "sum",
        "Total profit (%)": "mean",
        "Today Gain": "sum",
        "Today Gain (%)": "mean"
    }).reset_index()

    total_invested = grouped_df["Cost basis"].sum()
    total_current_value = grouped_df["Current value"].sum()
    total_profit = grouped_df["Total profit"].sum()
    total_today_gain = grouped_df["Today Gain"].sum()
    total_today_gain_percentage = (total_today_gain / total_current_value) * 100

    grouped_df["% in Portfolio"] = grouped_df["Cost basis"] / total_invested * 100

    price_columns = ["Buy rate ($/unit)", "Current rate ($/unit)", "Cost basis", "Current value", "Total profit", "Today Gain", "Today Gain (%)", "% in Portfolio"]
    grouped_df[price_columns] = grouped_df[price_columns].round(2)

    summary = {
        "Ticker": "Total",
        "Name": "",
        "Shares": grouped_df["Shares"].sum(),
        "Buy rate ($/unit)": "",
        "Current rate ($/unit)": "",
        "Cost basis": total_invested,
        "Current value": total_current_value,
        "Total profit": total_profit,
        "Today Gain": total_today_gain,
        "Today Gain (%)": total_today_gain_percentage,
        "% in Portfolio": grouped_df["% in Portfolio"].sum()
    }

    summary["Cost basis"] = round(summary["Cost basis"], 2)
    summary["Current value"] = round(summary["Current value"], 2)
    summary["Total profit"] = round(summary["Total profit"], 2)
    summary["Today Gain"] = round(summary["Today Gain"], 2)
    summary["Today Gain (%)"] = round(summary["Today Gain (%)"], 2)

    summary_df = pd.DataFrame([summary])
    return grouped_df, summary_df
