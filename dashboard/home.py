import streamlit as st
import os
from helpers.data import load_portfolios, save_portfolios, save_csv, load_csv, refresh_portfolio, merge_stocks
from helpers.stock import get_stock_info, get_historical_data, calculate_portfolio_value, calculate_sp500_comparison, get_etf_sector_weightings, get_analyst_recommendations, calculate_recommendation_percentages
from helpers.visualization import create_growth_plot, create_ticker_growth_plot, create_ytd_growth_chart, create_asset_allocation_pie_chart, create_sector_allocation_bar_chart
import pandas as pd



ALL_HOLDINGS_PORTFOLIO = "All Holdings"

def home(username):
    st.title(f"Stock Portfolio Management - Home ({username})")
    st.subheader("Create New Portfolio")
    portfolio_name = st.text_input("Portfolio Name", key="portfolio_name_input")

    portfolios = load_portfolios(username)

    if st.button("Create Portfolio"):
        if portfolio_name:
            if portfolio_name in portfolios:
                st.error("Portfolio with this name already exists.")
            else:
                portfolios[portfolio_name] = {"stocks": []}
                save_portfolios(username, portfolios)
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
                    if name != ALL_HOLDINGS_PORTFOLIO and os.path.exists(f'assets/{username}/{name}.csv'):
                        df = load_csv(username, name)
                        
                        df['Portfolio'] = name  # Add a column for the portfolio name
                        all_holdings.append(df)

                if all_holdings:
                    all_holdings_df = pd.concat(all_holdings, ignore_index=True)
                    if ALL_HOLDINGS_PORTFOLIO not in portfolios:
                        portfolios[ALL_HOLDINGS_PORTFOLIO] = {"stocks": all_holdings_df.to_dict(orient='records')}
                    else:
                        portfolios[ALL_HOLDINGS_PORTFOLIO]["stocks"] = all_holdings_df.to_dict(orient='records')
                    save_portfolios(username, portfolios)
                    df = refresh_portfolio(username, ALL_HOLDINGS_PORTFOLIO, portfolios[ALL_HOLDINGS_PORTFOLIO]["stocks"], get_stock_info)
                    # move the all holdings portfolio to the end of the list of portfolios
                    portfolios[ALL_HOLDINGS_PORTFOLIO] = portfolios.pop(ALL_HOLDINGS_PORTFOLIO)
                    save_portfolios(username, portfolios)
                    save_csv(username, ALL_HOLDINGS_PORTFOLIO, df)

    
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
                df = refresh_portfolio(username, portfolio_name, df.to_dict(orient='records'), get_stock_info)
                save_csv(username, portfolio_name, df)
                portfolios[portfolio_name]["stocks"] = df.to_dict(orient='records')
                save_portfolios(username, portfolios)
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
                Shares = st.number_input("No. of Shares", min_value=0.1, step=1.0, key="Shares_input", help="Enter the number of shares you own.", format="%.6f", placeholder="Type Here...")
                Buy_rate = st.number_input("Buy rate ($/unit)", min_value=0.01, step=0.01, key="Buy_rate_input", help="Enter the buy rate per unit.", format="%.2f")
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
                            df_1 = refresh_portfolio(username, portfolio_name, [stock], get_stock_info)
                            stock = df_1.to_dict(orient='records')[0]  # Correctly format the stock
                            portfolios[portfolio_name]["stocks"].append(stock)
                            save_portfolios(username, portfolios)
                            df = pd.DataFrame(portfolios[portfolio_name]["stocks"])
                            save_csv(username, portfolio_name, df)
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
                    save_portfolios(username, portfolios)
                    st.success(f"Portfolio '{selected_portfolio}' deleted successfully.")
                    
                    st.rerun()
