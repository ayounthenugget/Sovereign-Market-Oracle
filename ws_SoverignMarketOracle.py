import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# --- 1. THE REGIMES (The Mathematical Rules) ---
REGIMES = {
    'Conservative': {
        'z_window': 200, 'vol_window': 20, 'z_buy_gate': -1.5, 'z_sell_gate': 1.3, 'vol_gate': 1.25
    },
    'Aggressive': {
        'z_window': 50, 'vol_window': 10, 'z_buy_gate': -1.2, 'z_sell_gate': 1.1, 'vol_gate': 1.15
    }
}

# --- 2. THE ENGINE (The Math Class) ---
class SovereignMarketOracle:
    def __init__(self, tickers, regime_name='Conservative'):
        self.tickers = tickers
        self.regime = REGIMES.get(regime_name, REGIMES['Conservative'])
        self.benchmark_map = {'SOXL': 'SMH', 'PLTR': 'QQQ', 'TSLA': 'QQQ', 'LRCX': 'SMH'}

    def fetch_and_calculate(self, ticker):
        # Fetching 2 years of data for a solid baseline
        asset = yf.Ticker(ticker).history(period="2y").tz_localize(None)
        df = asset[['Close', 'High', 'Low', 'Volume']].rename(columns={'Close': 'price'})
        
        # Pulling Regime Parameters
        z_win, v_win = self.regime['z_window'], self.regime['vol_window']

        # Z-Score (Value)
        ma = df['price'].rolling(window=z_win).mean()
        std = df['price'].rolling(window=z_win).std()
        df['z_score'] = (df['price'] - ma) / std
        
        # Vol Ratio (Truth)
        df['vol_ratio'] = df['Volume'] / df['Volume'].rolling(window=v_win).mean()
        
        # MFI (Liquidity)
        df['mfi'] = ta.volume.MFIIndicator(df['High'], df['Low'], df['price'], df['Volume']).money_flow_index()
        
        # Pressure (Aggression)
        raw_force = (df['price'].diff(1) * df['Volume']).ewm(span=13).mean()
        df['pressure'] = raw_force / raw_force.rolling(window=50).std()
        
        latest = df.iloc[-1]
        z, vol, mfi, press = latest['z_score'], latest['vol_ratio'], latest['mfi'], latest['pressure']

        # Decision Matrix
        if z < self.regime['z_buy_gate'] and vol > self.regime['vol_gate']:
            status = "HIGH CONVICTION (BUY)"
        elif z < -0.8 and vol > 1.05:
            status = "ACCUMULATION (DCA)"
        elif z > self.regime['z_sell_gate']:
            status = "OVERBOUGHT (SELL/CASH)"
        else:
            status = "EQUILIBRIUM (HOLD)"

        return {
            "TICKER": ticker,
            "PRICE": round(latest['price'], 2),
            "Z-SCORE": round(z, 2),
            "VOL_RATIO": round(vol, 2),
            "PRESSURE": round(press, 2),
            "MFI": round(mfi, 2),
            "DECISION": status
        }

# --- 3. THE UI (Streamlit Dashboard) ---
st.set_page_config(page_title="Sovereign Oracle", layout="wide")
st.title("🏛️ Sovereign Market Oracle")

# Sidebar
st.sidebar.header("Oracle Configuration")
regime_choice = st.sidebar.selectbox("Select Regime", ["Conservative", "Aggressive"])
ticker_input = st.sidebar.text_input("Tickers (comma separated)", "VOO, SMH, TSCO, GE, LRCX, TSLA")

if st.sidebar.button("Execute Market Audit"):
    tickers = [t.strip().upper() for t in ticker_input.split(",")]
    oracle = SovereignMarketOracle(tickers, regime_name=regime_choice)
    
    results = []
    with st.spinner("Analyzing Market Microstructure..."):
        for ticker in tickers:
            try:
                results.append(oracle.fetch_and_calculate(ticker))
            except Exception as e:
                st.error(f"Error fetching {ticker}: {e}")
    
    if results:
        audit_df = pd.DataFrame(results)
        
        # Display the Main Table
        st.subheader(f"Audit Results: {regime_choice} Regime")
        st.dataframe(audit_df, use_container_width=True)
        
        # Visual Chart
        st.subheader("Institutional Aggression (Pressure)")
        st.bar_chart(audit_df.set_index('TICKER')['PRESSURE'])