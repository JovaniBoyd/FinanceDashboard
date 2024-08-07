Finance Tracker Dashboard
============
This program mainly utilizes the Plaid API to sync transactions across multiple banks for a monthly tracker.
It takes SQL data from a source file and outputs new data for the dashboard. Paths need to be specified for both databases.
Also utilizes CSS, Streamlit, Plost, and Yahoo Finance API to display data.

Functionality
-------
- Displays the amount spent each month and the percentage of each category in a pie chart
- Displays top five transactions and recurring transactions
- Uses .csv file to display networth
- Uses yfinance to display top performing stocks out of a list of personalized tickers



Jovani Boyd

Python 3.12.4

Usage
-------
This only works with transaction data in a SQL database formatted like the example.db file. 
This can be obtained through the Plaid API.
Add paths to databases and .csv files.
Add or remove tickers to list.
Run command:
  streamlit run streamlit_dash.py




