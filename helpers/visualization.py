import plotly.graph_objects as go
import pandas as pd

def create_growth_plot(username, portfolio_name, interval, total_invested, calculate_portfolio_value, calculate_sp500_comparison, load_csv, get_historical_data):
    portfolio_value = calculate_portfolio_value(username, portfolio_name, interval, load_csv, get_historical_data)
    initial_investment = portfolio_value['Total Portfolio Value'].iloc[0]
    current_value = portfolio_value['Total Portfolio Value'].iloc[-1]
    portfolio_percentage_increase = ((current_value - initial_investment) / initial_investment) * 100

    sp500_data = calculate_sp500_comparison(initial_investment, interval, get_historical_data)
    sp500_initial_value = sp500_data['Investment Value'].iloc[0]
    sp500_current_value = sp500_data['Investment Value'].iloc[-1]
    sp500_percentage_increase = ((sp500_current_value - sp500_initial_value) / sp500_initial_value) * 100

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=portfolio_value.index,
        y=portfolio_value['Total Portfolio Value'],
        mode='lines',
        name=f'{portfolio_name}',
        line=dict(color='green', width=2)             
    ))
    
    fig.add_shape(
        type="line",
        x0=portfolio_value.index[0],
        y0=total_invested,
        x1=portfolio_value.index[-1],
        y1=total_invested,
        line=dict(color="gray", width=1, dash="dash")
    )
    
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
    
    fig.update_layout(legend=dict(x=0, y=1.07, traceorder='normal'))
    fig.update_layout(legend=dict(orientation="h", bgcolor='rgba(0,0,0,0)'))
    
    fig.add_trace(go.Scatter(
        x=sp500_data.index,
        y=sp500_data['Investment Value'],
        mode='lines',
        name='S&P 500',
        line=dict(color='goldenrod', width=2)
    ))
    
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
    
    fig.update_layout(hovermode="x unified")
    
    fig.update_layout(
        title=f"Growth of {portfolio_name} Portfolio vs S&P 500 ({interval})",
        xaxis_title='Date',
        yaxis_title='Value',
        template='plotly_dark'
    )
    
    return fig

def create_ticker_growth_plot(ticker, interval, get_historical_data, buy_rate):
    historical_data = get_historical_data(ticker, period=interval)
    shares = 1  # Set shares to 1 for the purpose of growth visualization
    historical_data['Value'] = historical_data['Adj Close'] * shares
    initial_investment = historical_data['Value'].iloc[0]
    current_value = historical_data['Value'].iloc[-1]
    percentage_increase = ((current_value - initial_investment) / initial_investment) * 100
    
    fig = go.Figure()
    
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
        text=f"Buy Rate: ${buy_rate:.2f}",
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
    
    fig.update_layout(hovermode="x unified")
    
    fig.update_layout(
        title=f"Growth of {ticker} ({interval})",
        xaxis_title='Date',
        yaxis_title='Value',
        template='plotly_dark'
    )

    return fig



def create_ytd_growth_chart(ticker, get_historical_data):
    interval = "YTD"
    historical_data = get_historical_data(ticker, period=interval)
    shares = 1
    historical_data['Value'] = historical_data['Adj Close'] * shares
    initial_investment = historical_data['Value'].iloc[0]
    current_value = historical_data['Value'].iloc[-1]
    percentage_increase = ((current_value - initial_investment) / initial_investment) * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Value'],
        mode='lines',
        name=ticker,
        line=dict(color='green', width=2)
    ))
    
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
    
    fig.update_layout(
        title=f"YTD Growth of {ticker}",
        xaxis_title='Date',
        yaxis_title='Value',
        template='plotly_dark'
    )
    
    fig.update_layout(hovermode="x unified")

    return fig

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
    
    fig.update_traces(marker=dict(colors=['green', 'goldenrod', 'blue', 'red', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta', 'yellow', 'olive', 'navy', 'teal', 'maroon', 'gold', 'lime', 'indigo', 'silver']))
    fig.update_traces(textinfo='percent+label', textfont_size=12)
    return fig

def create_sector_allocation_bar_chart(merged_df, get_stock_info, get_etf_sector_weightings):
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
                        sector = sector.replace("_", " ").capitalize()
                        sector = sector.lower().title()
                        sectors.append(sector)
                        percentages.append(weight * row['Cost basis'])
        else:
            sector = stock_info.get('sector', 'Unknown')
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
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta', 'yellow', 'olive', 'navy', 'teal', 'maroon', 'gold', 'lime', 'indigo', 'silver']
    color_mapping = {sector: color for sector, color in zip(sector_allocation['Sector'].unique(), colors)}
    fig.update_traces(marker_color=[color_mapping[sector] for sector in sector_allocation['Sector']])
    
    return fig
