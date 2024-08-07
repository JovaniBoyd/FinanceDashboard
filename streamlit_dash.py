import streamlit as st
import pandas as pd
import plost
import yfinance as yf
from datetime import datetime
import sqlite3
import os

from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
# Stock tickers as a list of strings - add more if needed or delete
tickers_list = ['APPL', 'GOOGL', 'MCD', 'NKE','TSLA','TYL','VOO','VTI','VZ','WFC']
# Get current month
now = datetime.now()
current_month = now.strftime("%B")

# Paths for databases
fileName= r""# Path for the source database
newFile = r""# Path for the output database

# Connect to the database

cnn = sqlite3.connect(fileName)
cursor = cnn.cursor()
print('database connected...')
cursor.execute('''
DROP TABLE IF EXISTS prev_month
''' )
cursor.execute('''
CREATE TABLE prev_month (
category REAL,
date DATE,
name TEXT,
amount REAL
)
''' )
cursor.execute('''
DROP TABLE IF EXISTS curr_month
''' )
cursor.execute('''
CREATE TABLE curr_month (
category REAL,
date DATE,
name TEXT,
amount REAL
)
''' )
cursor.execute('''
INSERT INTO prev_month (category, date, name, amount)
SELECT category, date, name, amount
FROM transactions
WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now', 'start of month', '-1 month')
''')
cursor.execute('''
INSERT INTO curr_month (category, date, name, amount)
SELECT category, date, name, amount
FROM transactions
WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
''')


cnn.commit()
cnn.close() 

def createTotalsDB():
    cnn = None
    new_conn = None

    try:    
        cnn = sqlite3.connect(fileName)
        cursor = cnn.cursor()
        print('database connected...')

        cursor.execute('''
        SELECT category, SUM(amount) AS total_amount
        FROM transactions
        GROUP BY category
        ''')
        results = cursor.fetchall()

        cnn.close()

        print("creating new file")
    
        if os.path.exists(newFile):
            os.remove(newFile)
            print("file removed")

        new_conn = sqlite3.connect(newFile)
        new_cursor = new_conn.cursor()
        new_cursor.execute('''
        CREATE TABLE aggregated_totals (
        category TEXT PRIMARY KEY,
        total_amount REAL
        )
        ''' )
        new_cursor.executemany('''
        INSERT INTO aggregated_totals (category, total_amount)
        VALUES (?, ?)
        ''', results)
        new_conn.commit()
        new_conn.close()
    except Exception as e:
        print(e)
    finally:
        if cnn:
            cnn.close()

        if new_conn:
            new_conn.close()
        print('done')

def createTopFiveDB():
    cnn = None
    new_conn = None
    try:
        
        cnn = sqlite3.connect(fileName)
        cursor = cnn.cursor()
        cursor.execute('''       
        SELECT category, amount
        FROM curr_month
        ORDER BY amount DESC
        LIMIT 5
        ''')
        results = cursor.fetchall()
        new_conn = sqlite3.connect(newFile)
        new_cursor = new_conn.cursor()
        
        #To keep table with 5 rows insteading of adding 5 each time
        new_cursor.execute('''
        DROP TABLE IF EXISTS top_transactions
        ''' )

        new_cursor.execute('''
        CREATE TABLE IF NOT EXISTS top_transactions (
        category REAL, 
        amount REAL
        )
        ''')

        new_cursor.executemany('''
        INSERT INTO top_transactions (category, amount)
        VALUES (?, ?)
        ''', results)
        new_conn.commit()
        new_conn.close()

    except Exception as e:
        print(e)
    finally:
        if cnn:
            cnn.close()

        if new_conn:
            new_conn.close()
        print('done')

def createRecurring():
    cnn = None
    new_conn = None
    try:
        
        cnn = sqlite3.connect(fileName)
        cursor = cnn.cursor()
        # Added DISTINCT to avoid duplicates
        cursor.execute('''       
        SELECT DISTINCT t1.category, t1.name, t1.amount
        FROM curr_month AS t1
        JOIN prev_month AS t2
        ON t1.name = t2.name AND t1.amount = t2.amount
        ''')
        match_results = cursor.fetchall()
        print("Fetched results:", match_results)
    
        new_conn = sqlite3.connect(newFile)
        new_cursor = new_conn.cursor()
        
        #To keep table from duplicating data
        new_cursor.execute('''
        DROP TABLE IF EXISTS recurring
        ''' )

        new_cursor.execute('''
        CREATE TABLE IF NOT EXISTS recurring (
        category TEXT, 
        name TEXT,
        amount REAL
        )
        ''')

        new_cursor.executemany('''
        INSERT INTO recurring (category, name, amount)
        VALUES (?, ?, ?)
        ''', match_results)
        new_conn.commit()
        new_conn.close()

    except Exception as e:
        print(e)
    finally:
        if cnn:
            cnn.close()

        if new_conn:
            new_conn.close()
        print('done')


createTotalsDB()
createTopFiveDB()
createRecurring()

#=====================WEBAPP=====================

st.set_page_config(layout='wide', page_title="financial dash")

#CSS STYLING
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}


[data-testid="stMetric"] {
    background-color: #DBE2E9;
    text-align: left;
    padding: 20px 40px;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}


</style>
""", unsafe_allow_html=True)

conn = st.connection('finance_db', type='sql')

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    st.markdown(f'### {current_month}'.upper())
    total_a = conn.query('select* from aggregated_totals', ttl=timedelta(minutes=0.5))
    total_a['category']=total_a['category'].str.replace('_',' ')
    #st.dataframe(total_a)
    plost.pie_chart(
        data=total_a,
        theta='total_amount',
        color='category',
        legend='left',
        use_container_width=True
    )

with c2:
    st.markdown('### TOP TRANSACTIONS')
    top_5 = conn.query('select* from top_transactions', ttl=timedelta(minutes=0.5))
    top_5.index = top_5.index + 1
    top_5['category']=top_5['category'].str.replace('_',' ')
    st.dataframe(top_5,
                 column_order=("category", "amount"),
                 column_config={
                     "amount": st.column_config.NumberColumn(format="$%.2f")
                 })   
with c3:
    st.markdown('### RECURRING')
    rec = conn.query('select* from recurring', ttl=timedelta(minutes=0.5))
    rec.index = rec.index + 1
    rec['category']=rec['category'].str.replace('_',' ')
    st.dataframe(rec,
                 column_config={
                     "amount": st.column_config.NumberColumn(format="$%.2f")
                 })
    
# Row B Networth/Stocks

first_of_last_month = now.replace(day=1) - relativedelta(months=1)
first_of_month = now.replace(day=1)
earnings_data = {}
for ticker in tickers_list:
    stock = yf.Ticker(ticker)
    hist = stock.history(start=first_of_last_month, end=now)
    # Calculate earnings (closing price - opening price)
    if not hist.empty:
        earnings = hist['Close'][-1] - hist['Close'][0]
        earnings_data[ticker] = earnings
earnings_df = pd.DataFrame(list(earnings_data.items()), columns=['Ticker','Earnings'])
top_earnings_df = earnings_df.sort_values(by='Earnings', ascending=False).head(5)
top_5_earning_tickers = top_earnings_df['Ticker'].tolist()
stock_data = yf.download(top_5_earning_tickers, start=first_of_last_month, end=now)
d1, d2 = st.columns([1,2])
normalized_data = stock_data['Adj Close'] / stock_data['Adj Close'].iloc[0] * 100

with d1:
    st.markdown('### NETWORTH')
    netw = pd.read_csv('')#Add .csv file of balances (excel)
    st.dataframe(netw,
                    column_config={
                        "Amount": st.column_config.NumberColumn(format="$%d")
                    })
with d2:
    st.markdown('### STOCKS')
    st.line_chart(normalized_data)






    
