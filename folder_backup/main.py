import streamlit as st
import pandas as pd
import streamlit_antd_components as sac
from helpers.data import load_portfolios, save_portfolios, save_csv, load_csv, refresh_portfolio, merge_stocks
from helpers.stock import get_stock_info, get_historical_data, calculate_portfolio_value, calculate_sp500_comparison, get_etf_sector_weightings, get_analyst_recommendations, calculate_recommendation_percentages
from helpers.visualization import create_growth_plot, create_ticker_growth_plot, create_ytd_growth_chart, create_asset_allocation_pie_chart, create_sector_allocation_bar_chart
import os

# Constants
ALL_HOLDINGS_PORTFOLIO = "All Holdings"

# Main App
st.set_page_config(page_title="Stock Portfolio Management", layout="centered")

# Helper function to get cache key
def get_cache_key(portfolio_name, key):
    return f"{portfolio_name}_{key}"

# Load existing portfolios
portfolios = load_portfolios()

# Render Ant Design menu in the sidebar
with st.sidebar:
    st.title("Navigation")
    portfolio_items = [sac.MenuItem(name, icon='briefcase-fill') for name in portfolios.keys()]
    menu_items = [
        sac.MenuItem('Home', icon='house-fill'),
        sac.MenuItem('Portfolios', icon='box-fill', children=portfolio_items)
        
    ]
    selected_item = sac.menu(menu_items, open_all=True)

# Define page content based on selected menu item
if selected_item == 'Home':
    st.title("Stock Portfolio Management - Home")
    st.subheader("Create New Portfolio")
    portfolio_name = st.text_input("Portfolio Name", key="portfolio_name_input")

    if st.button("Create Portfolio"):
        if portfolio_name:
            if portfolio_name in portfolios:
                st.error("Portfolio with this name already exists.")
            else:
                portfolios[portfolio_name] = {"stocks": []}
                save_portfolios(portfolios)
                st.success("Portfolio created successfully.")
        else:
            st.error("Please enter a name for the portfolio.")
            
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader("Existing Portfolios")
    with col2:
        if len(portfolios) > 0:
            if st.button("Refresh"):
                all_holdings = []
                for name, data in portfolios.items():
                    if name != ALL_HOLDINGS_PORTFOLIO and os.path.exists(f'assets/{name}.csv'):
                        df = load_csv(name)
                        
                        df['Portfolio'] = name  # Add a column for the portfolio name
                        all_holdings.append(df)

                if all_holdings:
                    all_holdings_df = pd.concat(all_holdings, ignore_index=True)
                    if ALL_HOLDINGS_PORTFOLIO not in portfolios:
                        portfolios[ALL_HOLDINGS_PORTFOLIO] = {"stocks": all_holdings_df.to_dict(orient='records')}
                    else:
                        portfolios[ALL_HOLDINGS_PORTFOLIO]["stocks"] = all_holdings_df.to_dict(orient='records')
                    save_portfolios(portfolios)
                    df = refresh_portfolio(ALL_HOLDINGS_PORTFOLIO, portfolios[ALL_HOLDINGS_PORTFOLIO]["stocks"], get_stock_info)
                    # move the all holdings portfolio to the end of the list of portfolios
                    portfolios[ALL_HOLDINGS_PORTFOLIO] = portfolios.pop(ALL_HOLDINGS_PORTFOLIO)
                    save_portfolios(portfolios)
                    save_csv(ALL_HOLDINGS_PORTFOLIO, df)

    
    selected_portfolio = st.selectbox("Select Portfolio", list(portfolios.keys()), index=len(portfolios) - 1)
    if selected_portfolio:
        portfolio_name = selected_portfolio

    st.markdown("---")
    if portfolio_name in portfolios:
        st.subheader(f"Add Stocks to {portfolio_name}")
        # have 2 columns for the add stocks section
        
        
            
        # File uploader
        uploaded_file = st.file_uploader("##### Upload CSV", type=["csv"], key="csv_uploader")
        col1, col2 = st.columns([6, 1])
        # Submit button
        with col2:
            submit_button = st.button("Submit")

        if submit_button and uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                df = refresh_portfolio(portfolio_name, df.to_dict(orient='records'), get_stock_info)
                save_csv(portfolio_name, df)
                portfolios[portfolio_name]["stocks"] = df.to_dict(orient='records')
                save_portfolios(portfolios)
                st.success("Stocks added from CSV successfully.")                
                # Cl                
                # Refresh the UI
                # Refresh the page completely
                # clear the session state
            except Exception as e:
                st.error(f"Error loading CSV: {e}")



        st.markdown("##### Add Manually")

        if "Ticker_input" not in st.session_state:
            st.session_state.Ticker_input = ""

        Ticker = st.text_input("Ticker", key="Ticker_input", help="Type a Ticker and press search to verify.", placeholder="Type Here...").upper()

        if "search_clicked" not in st.session_state:
            st.session_state.search_clicked = False

        if st.button("Search Ticker"):
            st.session_state.search_clicked = True
            stock_info = get_stock_info(Ticker)
            st.session_state.stock_info = stock_info  # Save stock info to session state
            

        stock_info = st.session_state.get("stock_info", None)

        if stock_info and "longName" in stock_info:
            stock_info["currentPrice"] = round(stock_info["currentPrice"], 2)
            st.success(f"**{stock_info['longName']}** (Sector: {stock_info['sector']}, Current Price: ${stock_info['currentPrice']})")
            with st.expander("Read more:"):
                st.markdown(stock_info['longBusinessSummary'])
                st.plotly_chart(create_ytd_growth_chart(Ticker, get_historical_data))

            with st.form(key='add_stock_form'):
                Shares = st.number_input("No. of Shares", min_value=1, step=1, key="Shares_input")
                Buy_rate = st.number_input("Buy rate ($/unit)", min_value=0.01, step=0.01, key="Buy_rate_input")
                submit_button = st.form_submit_button(label='Add Stock')
                
                if submit_button:
                    if Shares > 0 and Buy_rate > 0:
                        # add spinner
                        with st.spinner("Adding stock..."):
                            stock = {
                                "Ticker": Ticker,
                                "Shares": Shares,
                                "Buy rate ($/unit)": Buy_rate,
                            }
                            df_1 = refresh_portfolio(portfolio_name, [stock], get_stock_info)
                            stock = df_1.to_dict(orient='records')[0]  # Correctly format the stock
                            portfolios[portfolio_name]["stocks"].append(stock)
                            save_portfolios(portfolios)
                            df = pd.DataFrame(portfolios[portfolio_name]["stocks"])
                            save_csv(portfolio_name, df)
                            st.success("Stock added successfully.")
                            st.session_state.search_clicked = False  # Reset search clicked state
                            # st.rerun()  # Refresh to update the UI
                    else:
                        st.error("Please fill all the fields.")
        elif st.session_state.search_clicked and stock_info is None:
            st.error("Ticker not found. Please try again.")

        
    if portfolios[portfolio_name].get("stocks"):
        st.subheader(f"Stocks in {portfolio_name}")
        df = pd.DataFrame(portfolios[portfolio_name]["stocks"])
        st.dataframe(df)

    if selected_portfolio:
        col1, col2 = st.columns([6, 1])
        with col1:
            if st.button("Delete Portfolio"):
                if selected_portfolio in portfolios:
                    del portfolios[selected_portfolio]
                    save_portfolios(portfolios)
                    st.success(f"Portfolio '{selected_portfolio}' deleted successfully.")
                    
                    st.rerun()
                    

elif selected_item in portfolios:
    portfolio_name = selected_item
    st.title(f"Portfolio Management - {portfolio_name}")

    if 'previous_selected_portfolio' not in st.session_state:
        st.session_state['previous_selected_portfolio'] = portfolio_name

    if portfolio_name != st.session_state['previous_selected_portfolio']:
        st.session_state.pop(get_cache_key(st.session_state['previous_selected_portfolio'], 'asset_allocation_fig'), None)
        st.session_state.pop(get_cache_key(st.session_state['previous_selected_portfolio'], 'sector_allocation_fig'), None)
        st.session_state.pop(get_cache_key(st.session_state['previous_selected_portfolio'], 'top_performers'), None)
        st.session_state.pop(get_cache_key(st.session_state['previous_selected_portfolio'], 'top_losers'), None)
        st.session_state.pop(get_cache_key(st.session_state['previous_selected_portfolio'], 'analyst_recommendations'), None)
        st.session_state['previous_selected_portfolio'] = portfolio_name

    if os.path.exists(f'assets/{portfolio_name}.csv'):
        df = load_csv(portfolio_name)
        merged_df, summary_df = merge_stocks(df)

        # Portfolio Stocks
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Portfolio Stocks")
        with col2:
            if st.button("Refresh", key="refresh_portfolio_stocks"):
                df = refresh_portfolio(portfolio_name, portfolios[portfolio_name]["stocks"], get_stock_info)
                merged_df, summary_df = merge_stocks(df)

        st.dataframe(merged_df)
        total_invested = summary_df["Cost basis"].values[0]
        total_current_value = summary_df["Current value"].values[0]
        total_profit = summary_df["Total profit"].values[0]
        total_profit_percentage = total_profit / total_invested * 100
        total_today_gain = summary_df["Today Gain"].values[0]
        total_today_gain_percentage = summary_df["Today Gain (%)"].values[0]

        col1, col2, col3, col4 = st.columns([1.1, 1.1, 0.8, 0.8])
        col1.metric("Total Invested", f"${total_invested}")
        col2.metric("Total Current Value", f"${total_current_value}")
        col3.metric("Total Profit", f"${total_profit}", f"{total_profit_percentage:.2f}%")
        col4.metric("Today", f"${total_today_gain}", f"{total_today_gain_percentage:.2f}%")

        time_intervals = ["1D", "5D", "1M", "3M", "YTD", "1Y", "2Y", "5Y", "MAX"]
        st.markdown("---")
        st.subheader("Portfolio Growth")
        st.text("Select Time Interval")

        if 'selected_interval' not in st.session_state:
            st.session_state.selected_interval = time_intervals[4]
        st.session_state.selected_interval = st.session_state.selected_interval

        cols = st.columns(len(time_intervals))
        for i, interval in enumerate(time_intervals):
            if cols[i].button(interval):
                st.session_state.selected_interval = interval

        selected_interval = st.session_state.selected_interval

        tickers = ['Entire Portfolio'] + df['Ticker'].unique().tolist()
        selected_ticker = st.selectbox("Select Ticker", tickers)
        if selected_ticker != 'Entire Portfolio':
            buy_rate = df.loc[df['Ticker'] == selected_ticker, 'Buy rate ($/unit)'].values[0]
            st.plotly_chart(create_ticker_growth_plot(selected_ticker, selected_interval, get_historical_data, buy_rate))
        else:
            st.plotly_chart(create_growth_plot(portfolio_name, selected_interval, total_invested, calculate_portfolio_value, calculate_sp500_comparison, load_csv, get_historical_data))
        st.markdown("---")

        # Asset and Sector Allocation
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Asset and Sector Allocation")
        with col2:
            if st.button("Refresh", key="refresh_asset_allocation"):
                st.session_state.pop(get_cache_key(portfolio_name, 'asset_allocation_fig'), None)
                st.session_state.pop(get_cache_key(portfolio_name, 'sector_allocation_fig'), None)

        asset_allocation_key = get_cache_key(portfolio_name, 'asset_allocation_fig')
        sector_allocation_key = get_cache_key(portfolio_name, 'sector_allocation_fig')

        if asset_allocation_key not in st.session_state:
            with st.spinner("Loading Asset Allocation..."):
                st.session_state[asset_allocation_key] = create_asset_allocation_pie_chart(merged_df)

        if sector_allocation_key not in st.session_state:
            with st.spinner("Loading Sector Allocation..."):
                st.session_state[sector_allocation_key] = create_sector_allocation_bar_chart(merged_df, get_stock_info, get_etf_sector_weightings)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(st.session_state[asset_allocation_key], use_container_width=True)
        with col2:
            st.plotly_chart(st.session_state[sector_allocation_key], use_container_width=True)

        st.markdown("---")

        # Today's Top Performers and Top Losers
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Today's Top Performers and Top Losers")
        with col2:
            if st.button("Refresh", key="refresh_top_performers"):
                st.session_state.pop(get_cache_key(portfolio_name, 'top_performers'), None)
                st.session_state.pop(get_cache_key(portfolio_name, 'top_losers'), None)

        top_performers_key = get_cache_key(portfolio_name, 'top_performers')
        top_losers_key = get_cache_key(portfolio_name, 'top_losers')

        if top_performers_key not in st.session_state or top_losers_key not in st.session_state:
            with st.spinner("Loading Today's Top Performers and Losers..."):
                top_performers = df[df['Today Gain'] > 0].nlargest(4, 'Today Gain')
                top_losers = df[df['Today Gain'] < 0].nsmallest(4, 'Today Gain')
                st.session_state[top_performers_key] = top_performers
                st.session_state[top_losers_key] = top_losers

        top_performers = st.session_state[top_performers_key]
        top_losers = st.session_state[top_losers_key]

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
                            col.metric(label=row["Ticker"], value=f"${row['Today Gain']:.2f}", delta=f"{row['Today Gain (%)']:.2f}%")

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
                            col.metric(label=row["Ticker"], value=f"${row['Today Gain']:.2f}", delta=f"{row['Today Gain (%)']:.2f}%")
        st.markdown("---")

        # Analyst Recommendations
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Analyst Recommendations")
        with col2:
            if st.button("Refresh", key="refresh_analyst_recommendations"):
                st.session_state.pop(get_cache_key(portfolio_name, 'analyst_recommendations'), None)

        analyst_recommendations_key = get_cache_key(portfolio_name, 'analyst_recommendations')

        if analyst_recommendations_key not in st.session_state:
            with st.spinner("Loading Analyst Recommendations..."):
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

                buy_recommendations.sort(key=lambda x: x[1], reverse=True)
                hold_recommendations.sort(key=lambda x: x[1], reverse=True)
                sell_recommendations.sort(key=lambda x: x[1], reverse=True)

                top_buy = buy_recommendations[:3]
                top_hold = hold_recommendations[:3]
                top_sell = sell_recommendations[:3]

                st.session_state[analyst_recommendations_key] = {
                    'top_buy': top_buy,
                    'top_hold': top_hold,
                    'top_sell': top_sell
                }

        top_buy = st.session_state[analyst_recommendations_key]['top_buy']
        top_hold = st.session_state[analyst_recommendations_key]['top_hold']
        top_sell = st.session_state[analyst_recommendations_key]['top_sell']

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
                st.metric(label=top_buy[1][0], value=f"{top_buy[1][1]:.2f}%", delta="Buy", delta_color="normal")
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
