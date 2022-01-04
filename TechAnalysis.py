import base64
import numpy as np
import streamlit as st
import datetime as dt
import yfinance as yf
import finplot as fplt


####################################################################
####################################################################
# Set up functions

def start_dt():
    today = dt.date.today()
    return today - dt.timedelta(days=365)

def end_dt():
    return dt.date.today()
    
def user_input_features():
    ticker = st.sidebar.text_input("Ticker", '^GSPC')
    start_date = st.sidebar.text_input("Start Date", start_dt())
    end_date = st.sidebar.text_input("End Date", end_dt())
    return ticker, start_date, end_date

def update_legend_text(x, y):
    row = df.loc[df.Date==x]
    # format html with the candle and set legend
    fmt = '<span style="color:#%s">%%.2f</span>' % ('0b0' if (row.Open<row.Close).all() else 'a00')
    rawtxt = '<span style="font-size:13px">%%s %%s</span> &nbsp; O%s C%s H%s L%s' % (fmt, fmt, fmt, fmt)
    hover_label.setText(rawtxt % (Ticker, '1D', row.Open, row.Close, row.High, row.Low))

def update_crosshair_text(x, y, xtext, ytext):
    ytext = '%s (Close%+.2f)' % (ytext, (y - df.iloc[x].Close))
    return xtext, ytext


####################################################################
####################################################################
# Set up other items

st.write("""
# Technical Analysis Dashboard
1. Populate the **ticker** box on the left with the ticker symbol you'd like data for. 
The ticker symbol should be consistent with how it's shown on Yahoo Finance e.g., S&P500 = ^GSPC.
2. Then provide the **time period** you're interested in.
3. Click **grab historical stock info** below for the historical info in a csv file.
""")

st.sidebar.header('User Input Parameters')

today = dt.date.today()

symbol, start, end = user_input_features()

download = st.button('Grab historical stock data and plot MACD')

if download:
    Ticker = symbol
    df = yf.download(Ticker, start=start, end=end)[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.fillna(method='pad', inplace=True)
    df.fillna(method='bfill', inplace=True)
    df.index.name = 'Date'
    df['Date'] = df.index
    df['Date'] = df['Date'].astype(np.int64)
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()

    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode()).decode()  # some strings
    linko = f'<a href="data:file/csv;base64,{b64}" download="Historical_Stock_Prices.csv">Download full csv file</a>'
    st.markdown(linko, unsafe_allow_html=True)

    st.header("MACD & Performance for "+symbol)
    # plot macd with standard colors first
    ax, ax2 = fplt.create_plot(symbol+' MACD', rows=2)
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACDSignalLine'] = df['MACD'].ewm(span=9).mean()
    df['Histogram'] = df['MACD'] - df['MACDSignalLine']
    fplt.volume_ocv(df[['Open', 'Close', 'Histogram']], ax=ax2, colorfunc=fplt.strength_colorfilter)
    fplt.plot(df['MACD'], ax=ax2, legend='MACD')
    fplt.plot(df['MACDSignalLine'], ax=ax2, legend='Signal')

    # change to b/w coloring templates for next plots
    fplt.candle_bull_color = fplt.candle_bear_color = '#000'
    fplt.volume_bull_color = fplt.volume_bear_color = '#333'
    fplt.candle_bull_body_color = fplt.volume_bull_body_color = '#fff'

    # plot price and volume
    fplt.candlestick_ochl(df[['Open', 'Close', 'High', 'Low']], ax=ax)
    hover_label = fplt.add_legend('', ax=ax)
    axo = ax.overlay()
    fplt.volume_ocv(df[['Open', 'Close', 'Volume']], ax=axo)
    fplt.plot(df.Volume.ewm(span=24).mean(), ax=axo, color=1)

    #######################################################
    ## update crosshair and legend when moving the mouse ##

    fplt.set_time_inspector(update_legend_text, ax=ax, when='hover')
    fplt.add_crosshair_info(update_crosshair_text, ax=ax)
    fplt.show()

    st.write("""
    • Data preview - click "Download full csv file" url above for full data dump:
    """)
    st.dataframe(df.head(5))