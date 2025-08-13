# app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Helper Functions ---

def calculate_rsi(data, period: int = 14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def calculate_bollinger_bands(data, period: int = 20):
    sma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return upper, lower

def format_number(value):
    if isinstance(value, (int, float)):
        return f"${value:,.0f}"
    return "N/A"

def format_percent(value):
    if isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    return "N/A"

# --- Streamlit UI ---

st.set_page_config(page_title="Simple Stock Analyzer", layout="wide")
st.title("📊 Simple Stock Analyzer")

# --- Sidebar Inputs ---
st.sidebar.header("Select Stock")
ticker = st.sidebar.text_input("Enter Ticker (e.g., AAPL, MSFT)", "AAPL")
start = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=365))
end = st.sidebar.date_input("End Date", datetime.now())

st.sidebar.header("Indicator Settings")
show_sma = st.sidebar.checkbox("Show Simple Moving Averages (SMA)", value=True)
show_ema = st.sidebar.checkbox("Show Exponential Moving Average (EMA 20)", value=False)
show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=True)


if st.sidebar.button("Analyze"):
    try:
        with st.spinner("Fetching data..."):
            stock = yf.Ticker(ticker)
            data = stock.history(start=start, end=end)
            info = stock.info

            if data.empty:
                st.warning("No data found for the given ticker.")
                st.stop()

        # --- Technical Indicators Calculation ---
        # SMAs
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        data['SMA200'] = data['Close'].rolling(window=200).mean()
        
        # EMA
        data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()

        # RSI and RSI Signal
        data['RSI'] = calculate_rsi(data)
        data['RSI_Signal'] = data['RSI'].ewm(span=9, adjust=False).mean()

        # MACD
        data['MACD'], data['Signal'], data['Hist'] = calculate_macd(data)
        
        # Bollinger Bands
        data['UpperBand'], data['LowerBand'] = calculate_bollinger_bands(data)

        # --- Price Chart ---
        st.subheader(f"📈 Price Chart – {ticker}")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name='Candlesticks', increasing_line_color='green', decreasing_line_color='red'))
        
        # Add indicators based on toggles
        if show_sma:
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA 20', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA 50', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name='SMA 200', line=dict(color='purple')))
        
        if show_ema:
            fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], name='EMA 20', line=dict(color='cyan', dash='dash')))
            
        if show_bb:
            fig.add_trace(go.Scatter(x=data.index, y=data['UpperBand'], name='Upper Band', line=dict(color='gray', dash='dot')))
            fig.add_trace(go.Scatter(x=data.index, y=data['LowerBand'], name='Lower Band', line=dict(color='gray', dash='dot')))
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, legend_title_text='Indicators')
        st.plotly_chart(fig, use_container_width=True)
        
        # --- Download Button ---
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=True).encode('utf-8')

        csv_data = convert_df_to_csv(data)
        st.download_button(
            label="📥 Download Plotted Data as CSV",
            data=csv_data,
            file_name=f'{ticker}_stock_data_{start.strftime("%Y%m%d")}_to_{end.strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )

        # --- RSI Chart with Signal Line ---
        st.subheader("📉 RSI (Relative Strength Index)")
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='red')))
        rsi_fig.add_trace(go.Scatter(x=data.index, y=data['RSI_Signal'], name='RSI Signal (9-EMA)', line=dict(color='yellow')))
        
        rsi_fig.add_hline(y=70, line_dash="dash", line_color="gray", annotation_text="Overbought")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="gray", annotation_text="Oversold")
        rsi_fig.update_layout(height=300, yaxis_title="RSI", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(rsi_fig, use_container_width=True)

        # Updated RSI Analysis
        rsi_latest = data['RSI'][-1]
        rsi_signal_latest = data['RSI_Signal'][-1]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Overbought/Oversold Analysis**")
            if rsi_latest > 70:
                st.warning(f"RSI is {rsi_latest:.1f} → The stock is likely **overbought**.")
            elif rsi_latest < 30:
                st.info(f"RSI is {rsi_latest:.1f} → The stock may be **oversold**.")
            else:
                st.success(f"RSI is {rsi_latest:.1f} → The stock is in a **healthy** range.")
        with col2:
            st.markdown("**RSI Signal Crossover Analysis**")
            if rsi_latest > rsi_signal_latest:
                st.success("RSI is above its Signal Line → **Bullish Momentum**.")
            else:
                st.warning("RSI is below its Signal Line → **Bearish Momentum**.")

        # --- MACD Chart ---
        st.subheader("📉 MACD (Trend Strength)")
        macd_fig = go.Figure()
        macd_fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='blue')))
        macd_fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal', line=dict(color='orange')))
        macd_fig.add_trace(go.Bar(x=data.index, y=data['Hist'], name='Histogram', marker_color='gray'))
        macd_fig.update_layout(height=300, yaxis_title="MACD", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(macd_fig, use_container_width=True)
        
        macd_now = data['MACD'][-1]
        signal_now = data['Signal'][-1]
        if macd_now > signal_now:
            st.success("MACD is above Signal → **Bullish signal**.")
        else:
            st.warning("MACD is below Signal → **Bearish signal** or weakening momentum.")

        # --- Volume ---
        st.subheader("📊 Volume")
        vol_fig = go.Figure()
        vol_fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume'))
        vol_fig.update_layout(height=300, yaxis_title="Volume")
        st.plotly_chart(vol_fig, use_container_width=True)

        avg_vol = data['Volume'].mean()
        today_vol = data['Volume'][-1]
        if today_vol > 1.5 * avg_vol:
            st.info("High volume today → Possible news or investor activity.")
        elif today_vol < 0.5 * avg_vol:
            st.info("Low volume today → Less interest.")
        else:
            st.info("Normal volume levels today.")

        # --- Fundamental Analysis ---
        with st.expander("📘 Fundamental Analysis", expanded=False):
            st.subheader("📌 Company Overview")
            st.markdown(f"- **Name:** {info.get('longName', 'N/A')}")
            st.markdown(f"- **Industry:** {info.get('industry', 'N/A')}")
            st.markdown(f"- **Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"- **Country:** {info.get('country', 'N/A')}")
            st.markdown(f"- **Summary:** {info.get('longBusinessSummary', 'No summary available')[:500]}...")

            st.subheader("💡 Key Financial Metrics")
            st.markdown(f"""
            - **Market Cap:** {format_number(info.get("marketCap"))}
            - **EPS (TTM):** {info.get("trailingEps", "N/A")}
            - **Dividend Yield:** {format_percent(info.get("dividendYield"))}
            - **Beta (Volatility):** {info.get("beta", "N/A")}
            - **52-Week Range:** ${info.get("fiftyTwoWeekLow", "N/A")} – ${info.get("fiftyTwoWeekHigh", "N/A")}
            - **Average Daily Volume:** {format_number(info.get("averageVolume"))}
            """)

            st.subheader("📈 Earnings Highlights")
            st.markdown(f"""
            - **Revenue (TTM):** {format_number(info.get("totalRevenue"))}
            - **Net Income (TTM):** {format_number(info.get("netIncomeToCommon"))}
            - **Profit Margin:** {format_percent(info.get("profitMargins"))}
            - **Free Cash Flow:** {format_number(info.get("freeCashflow"))}
            """)

            st.subheader("🧮 Valuation Ratios")
            st.markdown(f"""
            - **Trailing P/E:** {info.get("trailingPE", "N/A")}
            - **Forward P/E:** {info.get("forwardPE", "N/A")}
            - **PEG Ratio:** {info.get("pegRatio", "N/A")}
            - **Price-to-Sales Ratio:** {info.get("priceToSalesTrailing12Months", "N/A")}
            """)

            st.subheader("🏦 Balance Sheet Strength")
            st.markdown(f"""
            - **Total Assets:** {format_number(info.get("totalAssets"))}
            - **Total Liabilities:** {format_number(info.get("totalLiab"))}
            - **Debt-to-Equity Ratio:** {info.get("debtToEquity", "N/A")}
            - **Return on Equity (ROE):** {format_percent(info.get("returnOnEquity"))}
            """)

            st.subheader("🧠 Analyst Opinion")
            st.markdown(f"""
            - **Analyst Recommendation:** {info.get("recommendationKey", "N/A").capitalize()}
            - **Target Mean Price:** {format_number(info.get("targetMeanPrice"))}
            - **Number of Analysts:** {info.get("numberOfAnalystOpinions", "N/A")}
            - **Insider Ownership:** {format_percent(info.get("heldPercentInsiders"))}
            - **Institutional Ownership:** {format_percent(info.get("heldPercentInstitutions"))}
            """)

    except Exception as e:
        st.error(f"Something went wrong: {e}")
