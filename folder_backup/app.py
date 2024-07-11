import streamlit as st
import pandas as pd
import json
import os
import yfinance as yf
import plotly.graph_objects as go
from yahooquery import Ticker

# Constants
PORTFOLIOS_FILE = 'portfolios.json'

# Helper Functions
def load_portfolios():
    if os.path.exists(PORTFOLIOS_FILE):
        with open(PORTFOLIOS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_portfolios(portfolios):
    with open(PORTFOLIOS_FILE, 'w') as f:
        json.dump(portfolios, f)

def save_csv(portfolio_name, df):
    df.to_csv(f'{portfolio_name}.csv', index=False)

def load_csv(portfolio_name):
    return pd.read_csv(f'{portfolio_name}.csv')

def get_stock_info(Ticker):
    with st.spinner(f"Fetching data for {Ticker} from Yahoo Finance..."):
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
            # get after hours price 
            stock.info["currentPrice"] = stock.history(period='1d',prepost=False, interval="1m")['Close'].iloc[-1]
            return stock.info
        except KeyError:
            return None

def get_historical_data(ticker, period="1y"):
    # dictionary to convert 1M to 1mo
    period_dict = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "YTD": "YTD", "1Y": "1y", "2Y": "2y", "5Y": "5y", "MAX": "max"}
    period = period_dict[period]
    stock = yf.Ticker(ticker)
    if period == "1d":
        interval = "15m"
    elif period in ["5d", "1mo" ]:
        interval = "1d"
    elif period in ["3mo", "6mo", "1y", "YTD"]:
        interval = "1d"
    elif period in ["2y", "5y"]:
        interval = "1wk"
    else:
        interval = "1mo"
    
    historical_data = stock.history(period=period, interval=interval, prepost = False)
    if 'Adj Close' not in historical_data.columns:
        historical_data['Adj Close'] = historical_data['Close']
    historical_data.index = historical_data.index.tz_localize(None)  # Remove timezone information
    return historical_data


def refresh_portfolio(portfolio_name, stocks):
    updated_stocks = []
    for stock in stocks:
        Ticker = stock["Ticker"]
        Shares = float(stock["Shares"])
        Buy_rate = float(stock["Buy rate ($/unit)"])
        stock_info = get_stock_info(Ticker)
        if stock_info:
            current_price = stock_info["currentPrice"]
            if current_price == 'N/A':
                current_price = stock_info["previousClose"]
            current_price = float(current_price)
            cost_basis = Shares * Buy_rate
            current_value = Shares * current_price
            profit = current_value - cost_basis
            
            # Calculate today's gain
            previous_close = stock_info["previousClose"]
            today_gain = (current_price - previous_close) * Shares
            today_gain_percentage = ((current_price - previous_close) / previous_close) * 100
            
            updated_stocks.append({
                "Ticker": Ticker,
                "Name": stock_info["shortName"],
                "Type": stock_info["quoteType"],
                "Shares": Shares,
                "Buy rate ($/unit)": Buy_rate,
                "Current rate ($/unit)": current_price,
                "Cost basis": cost_basis,
                "Current value": current_value,
                "Total profit": profit,
                "Today Gain": today_gain,
                "Today Gain (%)": today_gain_percentage
            })
    df = pd.DataFrame(updated_stocks)
    save_csv(portfolio_name, df)
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
        "Today Gain": "sum",
        "Today Gain (%)": "mean"
    }).reset_index()

    total_invested = grouped_df["Cost basis"].sum()
    total_current_value = grouped_df["Current value"].sum()
    total_profit = grouped_df["Total profit"].sum()
    total_today_gain = grouped_df["Today Gain"].sum()
    total_today_gain_percentage = (total_today_gain / total_current_value) * 100

    grouped_df["% in Portfolio"] = grouped_df["Cost basis"] / total_invested * 100

    # make all price columns to 2 decimal places
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

    # round to 2 decimal places
    summary["Cost basis"] = round(summary["Cost basis"], 2)
    summary["Current value"] = round(summary["Current value"], 2)
    summary["Total profit"] = round(summary["Total profit"], 2)
    summary["Today Gain"] = round(summary["Today Gain"], 2)
    summary["Today Gain (%)"] = round(summary["Today Gain (%)"], 2)

    summary_df = pd.DataFrame([summary])
    # merged_df = pd.concat([grouped_df, summary_df], ignore_index=True)

    return grouped_df, summary_df


def calculate_portfolio_value(portfolio_name, interval):
    df = load_csv(portfolio_name)
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

def calculate_sp500_comparison(initial_investment, interval):
    sp500_data = get_historical_data("^GSPC", period=interval)
    sp500_initial_price = sp500_data['Adj Close'].iloc[0]
    sp500_data['Investment Value'] = (initial_investment / sp500_initial_price) * sp500_data['Adj Close']
    return sp500_data

def create_growth_plot(portfolio_name, interval, total_invested):
    portfolio_value = calculate_portfolio_value(portfolio_name, interval)
    initial_investment = portfolio_value['Total Portfolio Value'].iloc[0]
    current_value = portfolio_value['Total Portfolio Value'].iloc[-1]
    portfolio_percentage_increase = ((current_value - initial_investment) / initial_investment) * 100

    sp500_data = calculate_sp500_comparison(initial_investment, interval)
    sp500_initial_value = sp500_data['Investment Value'].iloc[0]
    sp500_current_value = sp500_data['Investment Value'].iloc[-1]
    sp500_percentage_increase = ((sp500_current_value - sp500_initial_value) / sp500_initial_value) * 100

    fig = go.Figure()
    
    # Add portfolio value data with green color
    fig.add_trace(go.Scatter(
        x=portfolio_value.index,
        y=portfolio_value['Total Portfolio Value'],
        mode='lines',
        name=f'{portfolio_name}',
        line=dict(color='green', width=2)             
    ))
    
    # add horizontal line for total invested
    fig.add_shape(
        type="line",
        x0=portfolio_value.index[0],
        y0=total_invested,
        x1=portfolio_value.index[-1],
        y1=total_invested,
        line=dict(color="gray", width=1, dash="dash")
    )
    # Add annotation for the total invested line
    fig.add_annotation(
        x=portfolio_value.index[0],
        y=total_invested,
        xref="x",
        yref="y",
        text=f"My buy value: ${total_invested:.2f}",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="gray")
    )
    # set position of the legend to top left
    fig.update_layout(legend=dict(x=0, y=1.07, traceorder='normal'))
    
    # make legend background transparent
    fig.update_layout(legend=dict(orientation="h", bgcolor='rgba(0,0,0,0)'))
    
    # Add S&P 500 data with golden color
    fig.add_trace(go.Scatter(
        x=sp500_data.index,
        y=sp500_data['Investment Value'],
        mode='lines',
        name='S&P 500',
        line=dict(color='goldenrod', width=2)
    ))
    # Add Portfolio percentage increase annotation with green color at the end of the line
    fig.add_annotation(
        x=portfolio_value.index[-1],
        y=current_value,
        xref="x",
        yref="y",
        text=f"{portfolio_percentage_increase:.1f}%",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="green")
    )
    # Add S&P 500 percentage increase annotation with golden color at the end of the line
    fig.add_annotation(
        x=sp500_data.index[-1],
        y=sp500_current_value,
        xref="x",
        yref="y",
        text=f"{sp500_percentage_increase:.1f}%",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="goldenrod")
    )
    # appear a verticle line whereever cursor is placed on the graph and show the y values of both the lines
    fig.update_layout(hovermode="x unified")
    
    # Add title and axis labels
    fig.update_layout(
        title=f"Growth of {portfolio_name} Portfolio vs S&P 500 ({interval})",
        xaxis_title='Date',
        yaxis_title='Value',
        template='plotly_dark'
    )
    
    st.plotly_chart(fig)

def create_ticker_growth_plot(ticker, interval):
    global merged_df  # Declare merged_df as global to access it within the function
    historical_data = get_historical_data(ticker, period=interval)
    shares = df.loc[df['Ticker'] == ticker, 'Shares'].sum()
    historical_data['Value'] = historical_data['Adj Close'] * shares
    initial_investment = historical_data['Value'].iloc[0]
    current_value = historical_data['Value'].iloc[-1]
    percentage_increase = ((current_value - initial_investment) / initial_investment) * 100
    
    # Get the buy rate for the ticker from merged_df
    buy_rate = merged_df.loc[merged_df['Ticker'] == ticker, 'Buy rate ($/unit)'].values[0]

    fig = go.Figure()
    
    # Add ticker value data with green color
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Value'],
        mode='lines',
        name=ticker,
        line=dict(color='green', width=2)
    ))

    # Add horizontal line for the buy rate
    fig.add_shape(
        type="line",
        x0=historical_data.index[0],
        y0=buy_rate * shares,
        x1=historical_data.index[-1],
        y1=buy_rate * shares,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    # Add annotation for the buy rate line
    fig.add_annotation(
        x=historical_data.index[0],
        y=buy_rate * shares,
        xref="x",
        yref="y",
        text=f"Buy rate: ${buy_rate:.2f}",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="gray")
    )
    
    # Add percentage increase annotation for ticker
    fig.add_annotation(
        x=historical_data.index[-1],
        y=current_value,
        xref="x",
        yref="y",
        text=f"{percentage_increase:.1f}%",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="green")
    )
    # appear a verticle line whereever cursor is placed on the graph and show the y values of both the lines
    fig.update_layout(hovermode="x unified")
    
    # Add title and axis labels
    fig.update_layout(
        title=f"Growth of {ticker} ({interval})",
        xaxis_title='Date',
        yaxis_title='Value',
        template='plotly_dark'
    )

    st.plotly_chart(fig)

def create_ytd_growth_chart(ticker):
    interval = "YTD"
    historical_data = get_historical_data(ticker, period=interval)
    shares = 1  # For illustration, assuming 1 share to show the growth percentage
    historical_data['Value'] = historical_data['Adj Close'] * shares
    initial_investment = historical_data['Value'].iloc[0]
    current_value = historical_data['Value'].iloc[-1]
    percentage_increase = ((current_value - initial_investment) / initial_investment) * 100
    
    fig = go.Figure()
    
    # Add ticker value data with green color
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Value'],
        mode='lines',
        name=ticker,
        line=dict(color='green', width=2)
    ))
    
    # Add percentage increase annotation for ticker
    fig.add_annotation(
        x=historical_data.index[-1],
        y=current_value,
        xref="x",
        yref="y",
        text=f"{percentage_increase:.1f}%",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="bottom",
        font=dict(color="green")
    )
    
    # Add title and axis labels
    fig.update_layout(
        title=f"YTD Growth of {ticker}",
        xaxis_title='Date',
        yaxis_title='Value',
        template='plotly_dark'
    )
    
    # vertical line whereever cursor is placed on the graph and show the y values of both the lines
    fig.update_layout(hovermode="x unified")

    st.plotly_chart(fig)

def create_asset_allocation_pie_chart(merged_df):
    asset_allocation = merged_df.groupby('Type')['Cost basis'].sum()

    fig = go.Figure(data=[go.Pie(
        labels=asset_allocation.index,
        values=asset_allocation.values,
        hole=.3
    )])

    fig.update_layout(
        title_text="Asset Allocation",
        annotations=[dict(text='Asset', x=0.5, y=0.5, font_size=20, showarrow=False)],
        template='plotly_dark'
    )
    # Set color for each asset type
    fig.update_traces(marker=dict(colors=['green', 'goldenrod', 'blue', 'red', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta', 'yellow', 'olive', 'navy', 'teal', 'maroon', 'gold', 'lime', 'indigo', 'silver']))
    
    # increase the font size percentage in the pie chart in side the pie chart
    fig.update_traces(textinfo='percent+label', textfont_size=12)
    return fig

def get_etf_sector_weightings(ticker):
    stock = Ticker(ticker)
    sector_weightings = stock.fund_holding_info.get(ticker, {}).get('sectorWeightings', [])
    return sector_weightings

def create_sector_allocation_bar_chart(merged_df):
    sectors = []
    percentages = []
    
    for index, row in merged_df.iterrows():
        ticker = row['Ticker']
        stock_info = get_stock_info(ticker)
        
        if row['Type'] == 'ETF':
            sector_weightings = get_etf_sector_weightings(ticker)
            if sector_weightings:
                for sector_weight in sector_weightings:
                    for sector, weight in sector_weight.items():
                        # Format the sector name
                        sector = sector.replace("_", " ").capitalize()
                        sector = sector.lower().title()
                        sectors.append(sector)
                        percentages.append(weight * row['Cost basis'])
        else:
            sector = stock_info.get('sector', 'Unknown')
            # Format the sector name
            sector = sector.lower().title()
            sectors.append(sector)
            percentages.append(row['Cost basis'])

    sector_allocation = pd.DataFrame({'Sector': sectors, 'Cost basis': percentages})
    sector_allocation = sector_allocation.groupby('Sector')['Cost basis'].sum().reset_index()


    
    fig = go.Figure(data=[go.Bar(
        x=sector_allocation['Sector'],
        y=sector_allocation['Cost basis'],
        textposition='auto'
    )])

    fig.update_layout(
        title_text="Sector Allocation",
        xaxis_title="Sector",
        yaxis_title="Cost Basis",
        template='plotly_dark'
    )
    
    # Set color for each sector based on the sector name
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta', 'yellow', 'olive', 'navy', 'teal', 'maroon', 'gold', 'lime', 'indigo', 'silver']
    color_mapping = {sector: color for sector, color in zip(sector_allocation['Sector'].unique(), colors)}
    fig.update_traces(marker_color=[color_mapping[sector] for sector in sector_allocation['Sector']])
    

    return fig

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

# Main App
st.set_page_config(page_title="Stock Portfolio Management", layout="centered")

# Load existing portfolios
portfolios = load_portfolios()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Portfolio"])

# Sidebar for Portfolio Selection
if page == "Portfolio":
    selected_portfolio = st.sidebar.selectbox("Select Portfolio", list(portfolios.keys()))
    st.sidebar.markdown("---")

# Home Page
if page == "Home":
    st.title("Stock Portfolio Management - Home")
    
    # Create New Portfolio
    st.header("Create New Portfolio")
    portfolio_name = st.text_input("Portfolio Name", key="portfolio_name_input")

    if st.button("Create Portfolio"):
        if portfolio_name:
            if portfolio_name in portfolios:
                st.error("Portfolio with this name already exists.")
            else:
                portfolios[portfolio_name] = {"stocks": []}
                save_portfolios(portfolios)
                st.success("Portfolio created successfully.")
                st.rerun()  # Refresh to update the sidebar

    # View Existing Portfolios
    st.header("Existing Portfolios")
    
    # select a by default first portfolio if pre
    # get the all the keys from the dictionary and select the first one
    selected_portfolio = st.selectbox("Select Portfolio", list(portfolios.keys()))
    if selected_portfolio:
        st.write(f"Selected Portfolio: {selected_portfolio}")
        portfolio_name = selected_portfolio
        

    st.markdown("---")
    
    # Add Stocks to Portfolio
    if portfolio_name and portfolio_name in portfolios:
        st.header(f"Add Stocks to {portfolio_name}")
        
        # Option to upload CSV
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                save_csv(portfolio_name, df)
                portfolios[portfolio_name]["stocks"] = df.to_dict(orient='records')
                save_portfolios(portfolios)
                st.success("Stocks added from CSV successfully.")
            except Exception as e:
                st.error(f"Error loading CSV: {e}")
                
        # Manual Stock Entry
        st.subheader("Add Manually")
        Ticker = st.text_input("Ticker", key="Ticker_input", help="Type a Ticker and press search to verify.",placeholder="Type Here...").upper()
        
        search_button = st.button("Search Ticker")
        stock_info = False
        if search_button:
            stock_info = get_stock_info(Ticker)
        if stock_info:
            # round to 2 decimal places
            stock_info["currentPrice"] = round(stock_info["currentPrice"], 2)
            st.success(f"**{stock_info['longName']}** (Sector: {stock_info['sector']}, Current Price: ${stock_info['currentPrice']})")
            
            # Summary always in expander
            with st.expander("Read more:"):
                st.markdown(stock_info['longBusinessSummary'])
                create_ytd_growth_chart(Ticker)
            # Show input for Shares and buy rate ($/unit) after successful search
            with st.form(key='add_stock_form'):
                Shares = st.number_input("No. of Shares", min_value=0.0, format="%.6f")
                Buy_rate = st.number_input("Buy Rate (per share in $)", min_value=0.0, format="%.2f")
                submit_button = st.form_submit_button(label='Add Stock')
            
                if submit_button:
                    if Shares > 0 and Buy_rate > 0 and stock_info:
                        stock = {"Ticker": Ticker, "Shares": Shares, "Buy rate ($/unit)": Buy_rate}
                        portfolios[portfolio_name]["stocks"].append(stock)
                        save_portfolios(portfolios)
                        df = refresh_portfolio(portfolio_name, portfolios[portfolio_name]["stocks"])
                        save_csv(portfolio_name, df)
                        st.success("Stock added successfully.")
                    else:
                        st.error("Please fill all the fields.")
            
        if stock_info is None:
            st.error("Ticker not found. Please try again.")

        # Display portfolio stocks
        if portfolios[portfolio_name].get("stocks"):
            st.subheader(f"Stocks in {portfolio_name}") 
            # add loading spinner            
            df = refresh_portfolio(portfolio_name, portfolios[portfolio_name]["stocks"])
            st.dataframe(df)
            

if page == "Portfolio" and selected_portfolio:
    st.title(f"Portfolio Management - {selected_portfolio}")
    
    if os.path.exists(f'{selected_portfolio}.csv'):
        df = load_csv(selected_portfolio)
        merged_df, summary_df = merge_stocks(df)
        col1, col2 = st.columns([6,1])
        with col1:
            st.subheader("Portfolio Stocks")
        with col2:
            if st.button("Refresh", key="refresh_button"):
                df = refresh_portfolio(selected_portfolio, portfolios[selected_portfolio]["stocks"])
                merged_df, summary_df = merge_stocks(df)
                # Clear cached charts when data is refreshed
                st.session_state.pop('asset_allocation_fig', None)
                st.session_state.pop('sector_allocation_fig', None)
        
        st.dataframe(merged_df)
        # Show total invested, current value, total profit (%)
        total_invested = summary_df["Cost basis"].values[0]
        total_current_value = summary_df["Current value"].values[0]
        total_profit = summary_df["Total profit"].values[0]
        total_profit_percentage = total_profit / total_invested * 100
        
        # Today's gain
        total_today_gain = summary_df["Today Gain"].values[0]
        total_today_gain_percentage = summary_df["Today Gain (%)"].values[0]
        
        col1, col2, col3, col4 = st.columns([1.1,1.1,0.8,0.8])
        
        col1.metric("Total Invested", f"${total_invested}")
        col2.metric("Total Current Value", f"${total_current_value}")
        col3.metric(
            "Total Profit",
            f"${total_profit}",
            f"{total_profit_percentage:.2f}%",
            
        )
        col4.metric(
            "Today",
            f"${total_today_gain}",
            f"{total_today_gain_percentage:.2f}%",
            
        )
        
        # Time interval selector and growth plot
        time_intervals = ["1D", "5D", "1M", "3M", "YTD" ,"1Y", "2Y", "5Y", "MAX"]
        st.markdown("---")
        st.subheader("Portfolio Growth")
        st.text("Select Time Interval")
        # Initialize the session state for the selected interval if it doesn't exist
        
        if 'selected_interval' not in st.session_state:
            st.session_state.selected_interval = time_intervals[4]  # Default to the 5th interval as per the original index
        # make it look selected
        st.session_state.selected_interval = st.session_state.selected_interval
        
        # Create a row of buttons for each time interval
        cols = st.columns(len(time_intervals))
        for i, interval in enumerate(time_intervals):
            # Use the index to access the specific column and create a button
            if cols[i].button(interval):
                # When a button is clicked, update the session state
                st.session_state.selected_interval = interval
        
        # Display the currently selected interval
        selected_interval = st.session_state.selected_interval

        # Dropdown for ticker selection
        tickers = ['Entire Portfolio'] + df['Ticker'].unique().tolist()
        selected_ticker = st.selectbox("Select Ticker", tickers)
        # Dropdown for ticker selection
        if selected_ticker == 'Entire Portfolio':
            create_growth_plot(selected_portfolio, selected_interval, total_invested)
        else:
            create_ticker_growth_plot(selected_ticker, selected_interval)
        st.markdown("---")
        
        # Add Asset Allocation and Sector Allocation charts
        st.subheader("Asset and Sector Allocation")
        if 'asset_allocation_fig' not in st.session_state:
            st.session_state['asset_allocation_fig'] = create_asset_allocation_pie_chart(merged_df)
        if 'sector_allocation_fig' not in st.session_state:
            st.session_state['sector_allocation_fig'] = create_sector_allocation_bar_chart(merged_df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(st.session_state['asset_allocation_fig'], use_container_width=True)
        with col2:
            st.plotly_chart(st.session_state['sector_allocation_fig'], use_container_width=True)
        
        st.markdown("---")
        
        # Add Top Performers and Top Losers Section
        # Add Top Performers and Top Losers Section
        st.subheader("Today's Top Performers and Top Losers")
        if not df.empty:
            top_performers = df[df['Today Gain'] > 0].nlargest(4, 'Today Gain')
            top_losers = df[df['Today Gain'] < 0].nsmallest(4, 'Today Gain')
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Top Performers")
                if top_performers.empty:
                    st.markdown("No performers today.")
                else:
                    for i in range(0, len(top_performers), 2):
                        cols = st.columns(2)
                        for idx, col in enumerate(cols):
                            if i + idx < len(top_performers):
                                row = top_performers.iloc[i + idx]
                                col.metric(
                                    label=row["Ticker"],
                                    value=f"${row['Today Gain']:.2f}",
                                    delta=f"{row['Today Gain (%)']:.2f}%"
                                )
            
            with col2:
                st.markdown("### Top Losers")
                if top_losers.empty:
                    st.markdown("No losers today.")
                else:
                    for i in range(0, len(top_losers), 2):
                        cols = st.columns(2)
                        for idx, col in enumerate(cols):
                            if i + idx < len(top_losers):
                                row = top_losers.iloc[i + idx]
                                col.metric(
                                    label=row["Ticker"],
                                    value=f"${row['Today Gain']:.2f}",
                                    delta=f"{row['Today Gain (%)']:.2f}%"
                                )
        st.markdown("---")

        # Add Analyst Recommendations Section
        st.subheader("Analyst Recommendations")
        buy_recommendations = []
        hold_recommendations = []
        sell_recommendations = []
        
        for ticker in merged_df['Ticker'].unique():
            recommendations = get_analyst_recommendations(ticker)
            if recommendations is not None:
                percentages = calculate_recommendation_percentages(recommendations)
                buy_recommendations.append((ticker, percentages['Buy']))
                hold_recommendations.append((ticker, percentages['Hold']))
                sell_recommendations.append((ticker, percentages['Sell']))

        # Sort and get top 3 recommendations for each category
        buy_recommendations.sort(key=lambda x: x[1], reverse=True)
        hold_recommendations.sort(key=lambda x: x[1], reverse=True)
        sell_recommendations.sort(key=lambda x: x[1], reverse=True)

        top_buy = buy_recommendations[:3]
        top_hold = hold_recommendations[:3]
        top_sell = sell_recommendations[:3]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("## Buy")
            st.markdown("##### ")
            st.markdown("## Hold")
            st.markdown("##### ")
            st.markdown("## Sell")

        with col2:
            
            if top_buy:
                st.metric(label=top_buy[0][0], value=f"{top_buy[0][1]:.2f}%", delta="Buy", delta_color="normal")
            else:
                st.markdown("N/A")
            if top_hold:
                st.metric(label=top_hold[0][0], value=f"{top_hold[0][1]:.2f}%", delta="Hold", delta_color="off")
            else:
                st.markdown("N/A")
            if top_sell:
                st.metric(label=top_sell[0][0], value=f"{top_sell[0][1]:.2f}%", delta="Sell", delta_color="inverse")
            else:
                st.markdown("N/A")

        with col3:
            
            if len(top_buy) > 1:
                st.metric(label=top_buy[1][0], value=f"{top_buy[1][1]:.2f}%", delta="Buy",delta_color="normal")
            else:
                st.markdown("N/A")
            if len(top_hold) > 1:
                st.metric(label=top_hold[1][0], value=f"{top_hold[1][1]:.2f}%", delta="Hold", delta_color="off")
            else:
                st.markdown("N/A")
            if len(top_sell) > 1:
                st.metric(label=top_sell[1][0], value=f"{top_sell[1][1]:.2f}%", delta="Sell", delta_color="inverse")
            else:
                st.markdown("N/A")

        with col4:
            
            if len(top_buy) > 2:
                st.metric(label=top_buy[2][0], value=f"{top_buy[2][1]:.2f}%", delta="Buy", delta_color="normal")
            else:
                st.markdown("N/A")
            if len(top_hold) > 2:
                st.metric(label=top_hold[2][0], value=f"{top_hold[2][1]:.2f}%", delta="Hold", delta_color="off")
            else:
                st.markdown("N/A")
            if len(top_sell) > 2:
                st.metric(label=top_sell[2][0], value=f"{top_sell[2][1]:.2f}%", delta="Sell", delta_color="inverse")
            else:
                st.markdown("N/A")

    else:
        st.write("No data available for this portfolio.")


        
        
        