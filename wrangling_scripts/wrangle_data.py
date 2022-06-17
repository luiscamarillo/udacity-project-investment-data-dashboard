#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import yfinance as yf  
import dateparser
import os
# import datetime as dt
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objs as go

import warnings
warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)

def create_charts():
    """Clean and prepare GBM+ style transaction history csv files to create four plotly figures, and a dictionary with key data.

    Args:
        None

    Returns:
        figures: list containing the four plotly visualizations
        values_dict: dictionary with key values and pandas dataframe with summary

    """
    # # Import Investment Data

    # Import all csv files in data folder
    #ath = os.path.dirname(os.path.abspath(os.getcwd()))
    
    files = os.listdir('data')

    dfs = []

    for filename in files:
        df = pd.read_csv(f"data/{filename}")
        dfs.append(df)


    # Create single df wiht all investment data available
    transactions_df = pd.concat(dfs)


    # # Data Preparation

    # Keep only buying transaction
    transactions_df.dropna(inplace=True)
    transactions_stocks_df = transactions_df[transactions_df['Descripción'] == "Compra de Acciones."]
    # Rename cols
    transactions_stocks_df.columns = ['STOCK', 'DATE', 'TIME', 'DESCRIPTION', 'TITLES', 'PRICE', 
                                      'RATE', 'TERM', 'INTEREST', 'TAXES', 'FEES', 'AMOUNT', 'BALANCE']
    # Keep only relevant cols
    transactions_stocks_df = transactions_stocks_df[['STOCK', 'DATE', 'TITLES', 'PRICE', 
                                                     'TAXES', 'FEES', 'AMOUNT']].reset_index(drop=True)
    # Convert values to numeric
    for col in ['PRICE', 'TAXES', 'FEES', 'AMOUNT']:
        transactions_stocks_df[col] = transactions_stocks_df[col].str.replace(',', '', regex=False)                                                              .str.replace('$', '', regex=False).astype(float)

    # Parse dates in Spanish
    transactions_stocks_df['DATE'] = transactions_stocks_df['DATE'].apply(lambda x: dateparser.parse(x))
    transactions_stocks_df.sort_values('DATE', inplace=True)

    # Add ".MX" to ticker to consult BMV
    transactions_stocks_df['STOCK'] = transactions_stocks_df['STOCK'].str[:-2] + '.MX'

    # Convert number of titles bought to numeric
    transactions_stocks_df['TITLES'] = pd.to_numeric(transactions_stocks_df['TITLES'])

    # Total invested
    transactions_stocks_df['INVESTED'] = round(transactions_stocks_df['PRICE'] * transactions_stocks_df['TITLES'], 2)


    # # Creating graphs

    # ## Invested per month

    # Get a dataframe with total amount of money invested each month.

    monthly_investments_df = transactions_stocks_df.groupby([transactions_stocks_df.DATE.dt.to_period('M')]).sum().reset_index()

    # Make sure we have every month between first month and today
    all_months_df = pd.DataFrame(pd.date_range(start = monthly_investments_df.DATE.min().to_timestamp(), 
                                     end = datetime.now(), freq='M'), columns=['DATE'])

    all_months_df['DATE'] = all_months_df['DATE'].dt.to_period('M')

    # Merge to add all months
    monthly_investments_df = all_months_df.merge(monthly_investments_df, how='left')

    # Fills nas w/ 0 in case a month is empty
    monthly_investments_df[monthly_investments_df.columns[1:]] = monthly_investments_df[monthly_investments_df.columns[1:]]                                                                                    .fillna(0)


    # ### Investment per month chart
    # Line chart with Date (month) on x-axis, amount invested (pesos) in y-axis.

    graph_one = []

    graph_one.append(
          go.Scatter(
          x = monthly_investments_df.DATE.astype(str).tolist(),
          y = round(monthly_investments_df.AMOUNT).tolist(),
          )
        )


    layout_one = dict(title = 'Amount Invested per Month',
                xaxis = dict(title = 'Date'),
                yaxis = dict(title = 'Pesos ($)'),
                )


    # ## Portfolio value over time
    # Create dataframe with portfolio value over time based on number of shares owned cumulative since the first date, and actual value of stock per day.

    # Get list of unique stocks in portfolio
    stocks_cols = transactions_stocks_df.STOCK.unique().tolist()

    # Download financial data for each stock per day, starting from the first date with available data
    yesterday = datetime.today() - timedelta(days=1)
    stocks_df = yf.download(stocks_cols, transactions_stocks_df.DATE.min(), yesterday, progress=False)

    # Keep only Adjusted Close, ie, final price of stock for the day
    stocks_close_df = stocks_df[['Adj Close']]

    # Fix multi-index to keep, add suffix per stock to signify closin price
    if len(stocks_cols) > 1:
        stocks_close_df.columns = stocks_close_df.columns.get_level_values(1)
    else:
        stocks_close_df.columns = stocks_cols

    stocks_close_df = stocks_close_df.add_suffix('_CLOSE').reset_index()
    stocks_close_df.rename(columns={'Date':'DATE'}, inplace=True)


    # Create cummulative dataframe with transactions data, keeping only stocks, date, and titles cols
    cum_stocks_df = transactions_stocks_df[['STOCK', 'DATE', 'TITLES']]

    # Groupby per date to find how many titles of each stock were bought per day, regardless of number of transactions
    cum_stocks_df = cum_stocks_df.groupby(['STOCK', 'DATE'], as_index=False).sum()

    # Add a cummulative counter of titles owned per stock each transaction day
    cum_stocks_df['CUM_TITLES'] = cum_stocks_df.groupby(['STOCK'])['TITLES'].cumsum()


    # Create pivot table from cumulative stocks to create a col per stock ticker, with titles owned as data per date
    cum_stocks_pivot_df = pd.pivot_table(cum_stocks_df, index='DATE', columns='STOCK', 
                                         values='CUM_TITLES', aggfunc='sum').reset_index()
    # Fill forward, to maintain cummulative tracking in case new shares aren't bought each transaction date
    cum_stocks_pivot_df.fillna(method='ffill', inplace=True)

    # Add titles bought to closing data per stock, get data for every day, including days where not shares were bought
    # Fill nans forward to populate titles held on days with no transactions, then fill in the first days with 0
    cum_stocks_close_df = stocks_close_df.merge(cum_stocks_pivot_df, how='left').fillna(method='ffill').fillna(0)


    # Get cols with closing price data
    stocks_close_cols = [f"{stock}_CLOSE" for stock in stocks_cols]

    # Multiply numbers of titles held per stock with stock value at given day, 
    # then add it all up to find total portfolio value for each given day
    cum_stocks_close_df['PORTFOLIO_VALUE'] = (cum_stocks_close_df[stocks_cols] * cum_stocks_close_df[stocks_close_cols].values)                                          .sum(axis=1)


    # ### Total portfolio value over time chart
    # Line chart with Date (days) on x-axis, total portfolio value (pesos) in y-axis.

    graph_two = []

    graph_two.append(
          go.Scatter(
          x = cum_stocks_close_df.DATE.astype(str).tolist(),
          y = round(cum_stocks_close_df.PORTFOLIO_VALUE).tolist(),
          )
        )


    layout_two = dict(title = 'Portfolio Value over Time',
                xaxis = dict(title = 'Date'),
                yaxis = dict(title = 'Pesos ($)'),
                )


    # ## Portfolio
    # Create dataframe with total value, titles, and allocation percentage per stock in portfolio

    # Get number of titles per stock
    portfolio_df = transactions_stocks_df.groupby('STOCK', as_index=False).sum()

    # Get current prices per stock, from latest date in stocks_close_df
    curr_prices = []
    for stock_ticker in portfolio_df.STOCK:
        curr_price = stocks_close_df[stocks_close_df.DATE == stocks_close_df.DATE.max()][f'{stock_ticker}_CLOSE'].iloc[0]
        curr_prices.append(curr_price)

    # Add current prices
    portfolio_df['CURRENT_PRICE'] = curr_prices

    # Get current value of portfolio per stock based on current prices
    portfolio_df['CURRENT_VALUE'] = round(portfolio_df['CURRENT_PRICE'] * portfolio_df['TITLES'], 2)

    # Add totals row
    portfolio_df = portfolio_df.append(portfolio_df.sum(numeric_only=True), ignore_index=True).fillna('Total')

    # Compute portfolio returns and percentage returns
    portfolio_df['RETURNS'] = round(portfolio_df['CURRENT_VALUE'] - portfolio_df['AMOUNT'], 2)
    portfolio_df['PER_RETURNS'] = round(portfolio_df['RETURNS']/portfolio_df['AMOUNT']*100, 2)

    # Extract total current portfolio value
    current_porfolio_value = portfolio_df.query('STOCK == "Total"')['CURRENT_VALUE'].iloc[0]

    # Get stock allocation percentage within portfolio
    portfolio_df['PER_PORTAFOLIO'] = round(portfolio_df['CURRENT_VALUE'] / current_porfolio_value*100, 2)


    # ### Total portfolio value over time chart
    # Bar chart with Stocks on x-axis, allocation percentage in y-axis.

    graph_three = []

    graph_three.append(
          go.Bar(
          x = portfolio_df[portfolio_df.STOCK != 'Total'].STOCK.tolist(),
          y = portfolio_df[portfolio_df.STOCK != 'Total'].PER_PORTAFOLIO.tolist(),
          )
        )


    layout_three = dict(title = 'Portfolio Allocation',
                xaxis = dict(title = 'Stocks'),
                yaxis = dict(title = 'Allocation (%)'),
                )


    # ## Monthly Returns
    # 
    # Create dataframes with monthly returns and value per month.

    # Groupby transactions df per month, stock, add up amount invested
    monthly_spent_df = transactions_stocks_df.groupby([transactions_stocks_df.DATE.dt.to_period('M'), 'STOCK']).sum().reset_index()

    # Create cummulative amount of titles held each month
    monthly_spent_df[['CUM_TITLES']] = monthly_spent_df.groupby(['STOCK'])[['TITLES']].cumsum()


    # Create pivot table with a column for each stock held, with cummulative titles as values
    cum_monthly_titles_df = pd.pivot_table(monthly_spent_df, index='DATE', columns='STOCK',
                                          values=['CUM_TITLES'], aggfunc='sum').reset_index().reset_index(drop=True)

    # Fix the multi-level index
    cum_monthly_titles_df.columns = cum_monthly_titles_df.columns.droplevel(0)
    cum_monthly_titles_df.rename(columns={'':'DATE'}, inplace=True)

    # Forward fill to keep cummulative titles in case no stocks bough in a given month
    cum_monthly_inv_df = cum_monthly_titles_df.fillna(method='ffill')

    # Merge wiht monthly_investments_df to get amount invested per month
    cum_monthly_inv_df = cum_monthly_inv_df.merge(monthly_investments_df[['DATE', 'AMOUNT']])

    # Add up cummulative invested amount for running total
    cum_monthly_inv_df['CUM_AMOUNT'] = cum_monthly_inv_df['AMOUNT'].cumsum()

    # Fill nans with 0 for numeric cols
    cum_monthly_inv_df[cum_monthly_inv_df.columns[1:]] = cum_monthly_inv_df[cum_monthly_inv_df.columns[1:]].fillna(0)

    # Get adjusted close per stock for the last day of each month
    monthly_stocks_close_df = stocks_close_df.groupby([stocks_close_df.DATE.dt.to_period('M')]).last()                           .rename(columns={'DATE':'DAY'}).reset_index().drop('DAY', axis=1)

    # Merge monthly portfolio with monthly adjusted closes
    monthly_inv_gains_df = monthly_stocks_close_df.merge(cum_monthly_inv_df, how='left').fillna(method='ffill')

    # Get monthly portfolio value pero month, multiplying number of titles times adjusted close
    monthly_inv_gains_df['PORTFOLIO_VALUE'] = (monthly_inv_gains_df[stocks_cols] * monthly_inv_gains_df[stocks_close_cols].values)                                          .sum(axis=1)

    # Calculate monthly returns
    monthly_inv_gains_df['RETURNS'] = round(monthly_inv_gains_df['PORTFOLIO_VALUE'] - monthly_inv_gains_df['CUM_AMOUNT'], 2)
    monthly_inv_gains_df['PER_RETURNS'] = round(monthly_inv_gains_df['RETURNS']/monthly_inv_gains_df['CUM_AMOUNT']*100, 2)

    # Add colors -- red when negative, green when positive
    monthly_inv_gains_df['COLOR'] = np.where(monthly_inv_gains_df['PER_RETURNS']<0, '#BC243C', '#88B04B')


    # ### Monthly Investment Returns chart
    # Bar/line chart with month on x-axis, returns and percentage returns in y-axes.

    graph_four = []

    graph_four.append(
          go.Bar(
          x = monthly_inv_gains_df.DATE.astype(str).tolist(),
          y = monthly_inv_gains_df.PER_RETURNS.tolist(),
          marker_color = monthly_inv_gains_df['COLOR'],
          yaxis='y',
          name='Investment Returns Rate')
        )

    # Add second layer with line chart on total money return with secondary axis
    graph_four.append(
          go.Scatter(
          x = monthly_inv_gains_df.DATE.astype(str).tolist(),
          y = monthly_inv_gains_df.RETURNS.tolist(),
          yaxis='y2',
          name='Investment Returns ($)',
          marker_color = '#5B5EA6'
          )
        )

    layout_four = dict(title = 'Investment Returns per Month',
                xaxis = dict(title = 'Month'),
                yaxis1 = dict(title = 'Investment Returns Rate (%)'),
                yaxis2 = dict(title = 'Investment Returns ($)', overlaying="y", side='right')
                )


    # # Values

    # Get value for total returns, returns percentage, potential monthly investment income
    current_returns = portfolio_df.query('STOCK == "Total"')['RETURNS'].iloc[0]
    current_per_returns = portfolio_df.query('STOCK == "Total"')['PER_RETURNS'].iloc[0]
    monthly_income = round(current_porfolio_value*(0.04/12),2)

    # Create dataframe summary off portfolio_df
    total_summary_df = portfolio_df.T.reset_index()
    total_summary_df.columns = total_summary_df.loc[0]

    # Keep only relevant values, cols
    total_summary_df = total_summary_df[['STOCK', 'Total']]
    total_summary_df = total_summary_df[total_summary_df.STOCK.isin(['INVESTED', 'TAXES', 'FEES', 'AMOUNT'])]
    total_summary_df.columns = ['Category', 'Total']

    total_summary_df['Total'] = total_summary_df['Total'].apply(lambda x: "${:,}".format(round(x, 2)))


    # Replace with nicer strings
    total_summary_df.replace({
        'Category':{
            'INVESTED':'Total Invested',
            'TAXES': 'Witheld Taxes',
            'FEES': 'Fees',
            'AMOUNT': 'Total Spent'
        }
    }, inplace=True)

    # Order by category
    total_summary_df.Category = pd.Categorical(total_summary_df.Category,
                                           categories=["Total Invested", "Witheld Taxes", "Fees", "Total Spent"],
                                           ordered=True)
    total_summary_df.sort_values('Category', inplace=True)

    # Create dictionary with key values, total_summary_df
    values_dict = {
        'current_porfolio_value': "{:,}".format(round(current_porfolio_value, 2)),
        'current_returns': "{:,}".format(current_returns),
        'current_per_returns': current_per_returns,
        'monthly_income': "{:,}".format(monthly_income),
        'total_summary_df': total_summary_df.values.tolist()
    }

    # Append all charts to the figures list
    figures = []
    figures.append(dict(data=graph_one, layout=layout_one))
    figures.append(dict(data=graph_two, layout=layout_two))
    figures.append(dict(data=graph_three, layout=layout_three))
    figures.append(dict(data=graph_four, layout=layout_four))

    return figures, values_dict

