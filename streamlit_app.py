import streamlit as st
import pandas as pd
import feedparser
from nsepython import nse_eq
from streamlit_autorefresh import st_autorefresh
from concurrent.futures import ThreadPoolExecutor
from SmartApi import SmartConnect
import requests
import pyotp
import time
from datetime import datetime
from bs4 import BeautifulSoup as bs

# CONFIG
st.set_page_config(layout="wide")

# Sidebar filter
st.sidebar.markdown("### 📂 News Settings")
filter_term = st.sidebar.text_input("Filter by sector or stock (e.g. BANK, RELIANCE):").strip()

import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd

# -------------------
# OpenAI API Key
# -------------------
OPENAI_API_KEY = "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"


client = OpenAI(api_key=OPENAI_API_KEY)

st.title("📊 Nifty Present Sentiment with CPR (AI Powered)")

# -------------------
# Get Live Nifty Data
# -------------------
# -------------------
# Get Live Nifty Data
# -------------------
nifty = yf.Ticker("^NSEI")
data = nifty.history(period="2d", interval="1d")  # Yesterday + Today

try:
    prev_day = data.iloc[-2]
    prev_volume = prev_day["Volume"]

    today_intraday = nifty.history(period="1d", interval="1m")

    if not today_intraday.empty:
        current_price = today_intraday["Close"].iloc[-1]
        high_price = today_intraday["High"].max()
        low_price = today_intraday["Low"].min()
        change = current_price - today_intraday["Close"].iloc[0]
        change_percent = (change / today_intraday["Close"].iloc[0]) * 100

        today_data = data.iloc[-1]
        today_volume = today_data["Volume"]
        volume_change_percent = ((today_volume - prev_volume) / prev_volume) * 100

        # CPR
        high_y = prev_day["High"]
        low_y = prev_day["Low"]
        close_y = prev_day["Close"]

        pivot = (high_y + low_y + close_y) / 3
        bc = (high_y + low_y) / 2
        tc = (pivot + bc) / 2

        # Support / Resistance
        R1 = (2 * pivot) - low_y
        S1 = (2 * pivot) - high_y
        R2 = pivot + (high_y - low_y)
        S2 = pivot - (high_y - low_y)
        R3 = high_y + 2 * (pivot - low_y)
        S3 = low_y - 2 * (high_y - pivot)

        # Create DataFrame for table display
        table_data = {
            "Component": [
                "Current Nifty", "Change %", "Volume Change %",
                "Pivot (P)", "Top CPR (TC)", "Bottom CPR (BC)",
                "R1", "R2", "R3", "S1", "S2", "S3",
                "Prev Day High", "Prev Day Low", "Today High", "Today Low"
            ],
            "Value": [
                f"{current_price:.2f}", f"{change_percent:.2f}%",
                f"{volume_change_percent:.2f}%",
                f"{pivot:.2f}", f"{tc:.2f}", f"{bc:.2f}",
                f"{R1:.2f}", f"{R2:.2f}", f"{R3:.2f}",
                f"{S1:.2f}", f"{S2:.2f}", f"{S3:.2f}",
                f"{high_y:.2f}", f"{low_y:.2f}",
                f"{high_price:.2f}", f"{low_price:.2f}"
            ]
        }

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Unable to fetch live intraday Nifty data. Skipping Nifty table.")
except Exception as e:
    st.warning(f"Previous day Nifty data not available. Skipping Nifty table. ({e})")

# RSS Sources
RSS_FEEDS = {
    "LiveMint Markets": "https://www.livemint.com/rss/markets",
    "LiveMint Companies": "https://www.livemint.com/rss/companies",
    "MC Markets":     "https://www.moneycontrol.com/rss/business/markets/",
    "MC Nifty":       "https://www.moneycontrol.com/rss/tags/nifty.xml"
}

def fetch_and_filter(feeds, keyword):
    items = []
    for name, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            txt = (entry.title + " " + entry.get('summary', "")).lower()
            if not keyword or keyword.lower() in txt:
                items.append({
                    "source": name,
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", "")
                })
    return items

news_items = fetch_and_filter(RSS_FEEDS, filter_term)[:15]

# Display news
st.markdown("## 📰 Filtered India Stock News")
if filter_term:
    st.markdown(f"**Filtering news for:** `{filter_term}`")
for n in news_items:
    st.markdown(f"- [{n['title']}]({n['link']})  \n<sub>{n['source']} · {n['published']}</sub>", unsafe_allow_html=True)

# SECTOR STOCKS
sector_stocks = {
    "Agriculture sector": ['UPL',
'COROMANDEL',
'PIIND',
'CHAMBLFERT',
'SUMICHEM',
'BASF',
'BAYERCROP',
'RCF',
'GSFC',
'PARADEEPH',
'KSCL',
'BSHSL',
'NATHBIOGEN',
'JKAG',
'OSWALAGRO',
'RALLIS',
'DHANUKA',
'SHARDACROP',
'JUBILANT',
'BBTC',
'HARRMALAYA',
'INDUS',
'APISINDIA',
'VENKYS',
'TATACONSUM',
'GODREJAGRO'],
    "NIFTY AUTO": ['TATAMOTORS', 'EICHERMOT', 'BAJAJ-AUTO', 'M&M', 'TVSMOTOR', 'HEROMOTOCO', 'ASHOKLEY', 'BOSCHLTD', 'BHARATFORG', 'MRF'],
    "NIFTY BANK": ['HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'SBIN', 'PNB', 'BANKBARODA', 'FEDERALBNK', 'IDFCFIRSTB', 'INDUSINDBK'],
    "NIFTY FMCG": ['HINDUNILVR', 'ITC', 'DABUR', 'MARICO', 'NESTLEIND', 'BRITANNIA', 'COLPAL', 'TATACONSUM', 'UBL', 'GODREJCP'],
    "NIFTY PHARMA": ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA', 'BIOCON', 'ALKEM', 'LUPIN', 'ZYDUSLIFE', 'TORNTPHARM'],
    "NIFTY IT": ['INFY', 'TCS', 'WIPRO', 'TECHM', 'HCLTECH', 'LTIM', 'MPHASIS', 'PERSISTENT', 'COFORGE'],
    "NIFTY REALTY": ['DLF', 'OBEROIRLTY', 'LODHA', 'GODREJPROP', 'PHOENIXLTD', 'SOBHA', 'PRESTIGE', 'BRIGADE'],
    "NIFTY ENERGY": ['RELIANCE', 'ONGC', 'NTPC', 'POWERGRID', 'ADANIGREEN', 'ADANITRANS', 'TATAPOWER', 'BPCL', 'IOC', 'COALINDIA'],
    "NIFTY METAL": ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'COALINDIA', 'NMDC', 'VEDL', 'NATIONALUM', 'SAIL', 'JINDALSTEL'],
    "NIFTY MEDIA": ['ZEEL', 'SUNTV', 'PVRINOX', 'NETWORK18', 'TV18BRDCST'],
    "NIFTY FINANCIAL SERVICES": ['BAJFINANCE', 'HDFCAMC', 'ICICIPRULI', 'HDFCLIFE', 'SBILIFE', 'MUTHOOTFIN', 'BAJAJFINSV', 'CHOLAFIN']
}

def fetch_stock_data(stock_list):
    data = []
    for stock in stock_list:
        try:
            info = nse_eq(stock)
            last_price = float(info['priceInfo']['lastPrice'])
            prev_close = float(info['priceInfo']['previousClose'])
            change_pct = ((last_price - prev_close) / prev_close) * 100 if prev_close != 0 else 0
            data.append({
                "Stock": stock,
                "Last Price": round(last_price, 2),
                "Change (%)": round(change_pct, 2)
            })
        except:
            data.append({
                "Stock": stock,
                "Last Price": "NA",
                "Change (%)": "NA"
            })
    return pd.DataFrame(data)

def format_df(df):
    df["Last Price"] = df["Last Price"].astype(str).apply(lambda x: f"{float(x):.2f}" if x != "NA" else x)
    df["Change (%)"] = df["Change (%)"].astype(str).apply(lambda x: f"{float(x):.2f}%" if x != "NA" else x)
    return df.sort_values(by="Change (%)", ascending=False, key=lambda col: pd.to_numeric(col.str.replace('%', ''), errors='coerce').fillna(-999))

def color_change(val):
    try:
        if isinstance(val, str) and "%" in val:
            val = float(val.replace('%', ''))
        return "color: green" if val > 0 else "color: red"
    except:
        return ""

# DASHBOARD
st.title("📊 NSE Sector Scope Dashboard")
st.markdown("### Intraday Performance: All Stocks by Sector")

# Sector scope overview
sector_perf = []
with ThreadPoolExecutor() as executor:
    sector_data = dict(zip(
        sector_stocks.keys(),
        executor.map(fetch_stock_data, sector_stocks.values())
    ))

for sector, df in sector_data.items():
    change_col = pd.to_numeric(df['Change (%)'].replace("NA", pd.NA), errors='coerce')
    avg_change = change_col.mean(skipna=True)
    sector_perf.append({"Sector": sector, "Avg Change (%)": f"{round(avg_change, 2):.2f}%" if pd.notna(avg_change) else "NA"})

perf_df = pd.DataFrame(sector_perf).sort_values(by="Avg Change (%)", ascending=False, key=lambda x: pd.to_numeric(x.str.replace('%', ''), errors='coerce').fillna(-999))
st.markdown("### 📈 Sector Scope Overview")
st.dataframe(perf_df.style.map(color_change, subset=["Avg Change (%)"]), use_container_width=True, height=280)

cols = st.columns(3)
i = 0

for sector, df in sector_data.items():
    df = format_df(df)
    styled = df.style.map(color_change, subset=["Change (%)"])

    with cols[i]:
        st.markdown(f"#### {sector}")
        st.dataframe(styled, use_container_width=True, height=350)
    i = (i + 1) % 3
    if i == 0:
        cols = st.columns(3)
api_key = 'aRqJTcLY'
username = 'R116253'
pwd = '9900'
totp_token = "WAGBNYVQBSQK5OCVZ5D36HEF3Q"
TELEGRAM_TOKEN = '7639433886:AAHTQ8rn0WgLI2NGDh3bSadZAc5xhzpnlus'
TELEGRAM_CHAT_ID = '1476321797'

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        return response
    except Exception as e:
        st.error(f"⚠️ Telegram error: {e}")
        return None

# --- LOGIN SMART API ---
with st.spinner("🔐 Logging in to SmartAPI..."):
    try:
        smartApi = SmartConnect(api_key)
        totp = pyotp.TOTP(totp_token).now()
        session = smartApi.generateSession(username, pwd, totp)

        if not session['status']:
            st.error("❌ SmartAPI login failed.")
            st.stop()

        refreshToken = session['data']['refreshToken']
        feedToken = smartApi.getfeedToken()
        profile = smartApi.getProfile(refreshToken)
    except Exception as e:
        st.error(f"Login Error: {e}")
        st.stop()

# --- CHARTINK FETCH ---
st.title("📊 Near BreakOut")
with st.spinner("📥 Fetching Screener Results..."):
    url = "https://chartink.com/screener/process"
    condition = {
        "scan_clause": "( {33489} (      latest close > latest ema( latest close , 20 ) AND      latest close > latest ema( latest close , 50 ) AND       latest close >= 0.97 * greatest( latest high, 1 day ago high, 2 days ago high, 3 days ago high, 4 days ago high ) AND       latest volume > 1.5 * sma( latest volume , 20 ) AND      latest rsi( 14 ) > 55    )  )"

      #  "scan_clause": "( {33489} ( latest close > latest ema( latest close , 20 ) and latest close > latest ema( latest close , 50 ) and latest rsi( 14 ) > 50 and latest close <= greatest(  latest high, 1 day ago high, 2 days ago high, 3 days ago high, 4 days ago high, 5 days ago high, 6 days ago high, 7 days ago high, 8 days ago high, 9 days ago high, 10 days ago high, 11 days ago high, 12 days ago high, 13 days ago high, 14 days ago high, 15 days ago high, 16 days ago high, 17 days ago high, 18 days ago high, 19 days ago high  ) * 1.03 and latest close >= least(  latest low, 1 day ago low, 2 days ago low, 3 days ago low, 4 days ago low, 5 days ago low, 6 days ago low, 7 days ago low, 8 days ago low, 9 days ago low, 10 days ago low, 11 days ago low, 12 days ago low, 13 days ago low, 14 days ago low, 15 days ago low, 16 days ago low, 17 days ago low, 18 days ago low, 19 days ago low  ) * 0.97 and( 14 ) < latest sma( latest volume , 14 ) and latest close > 100 and latest volume >= 200000 and( {166311} not( latest close > 0 ) ) and (latest close - 1 candle ago close / 1 candle ago close * 100) >= 0 ) ) "
    }
    
  

    try:
        with requests.Session() as s:
            r = s.get(url)
            soup = bs(r.content, "lxml")
            meta = soup.find("meta", {"name": "csrf-token"})["content"]
            headers = {"x-csrf-token": meta}
            response = s.post(url, headers=headers, data=condition)
            chartink_data = pd.DataFrame(response.json()["data"])
    except Exception as e:
        st.error(f"Chartink Fetch Error: {e}")
        st.stop()

# --- PROCESS AND SEND ALERTS ---
if not chartink_data.empty:
    st.success(f"✅ Fetched {len(chartink_data)} results.")
    st.dataframe(chartink_data)

   # st.subheader("📬 Sending Telegram Alerts")
   # alert_count = 0
   # progress = st.progress(0)



    for idx, row in chartink_data.iterrows():
        try:
            time.sleep(1)
            search = smartApi.searchScrip("NSE", row['nsecode'] + "-EQ")
            
            if search.get("data"):
                for stock in search['data']:
                    token = stock.get("symboltoken")
                    symbol = stock.get("symbol", row["nsecode"])

                    if not token:
                        st.warning(f"⚠️ Token not found for {row['nsecode']}")
                        continue

                    mktdata = smartApi.getMarketData("FULL", {"NSE": [token]})

                    if mktdata["data"].get("fetched"):
                        d = mktdata["data"]["fetched"][0]
                        ltp = d.get("ltp")
                        high = d.get("high")
                        open_ = d.get("open")
                        low = d.get("low")

                        if None in (ltp, high, open_, low):
                            st.warning(f"⚠️ Incomplete data for {symbol}")
                            continue

                        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        gap = round(high - ltp, 2)
                        if ltp > low and gap > 10:
                            message = (
                                f"*📢 Stock Alert: {symbol}*\n\n"
                                f"🗓 Date: {date_str}\n"
                                f"▶️ LTP: ₹{ltp}\n"
                                f"📈 High: ₹{high}\n"
                                f"🟢 Open: ₹{open_}\n"
                                f"📉 Low: ₹{low}\n"
                                f"🔍 Gap: ₹{gap}"
                            )
                           # resp = send_telegram_message(message)
                           # if resp and resp.status_code == 200:
                           #     alert_count += 1
                            #else:
                            #    st.error(f"❌ Telegram failed: {resp.status_code if resp else 'Unknown error'}")
            else:
                st.warning(f"⚠️ No data found for {row['nsecode']}")
        except Exception as e:
            st.warning(f"❗ Error processing {row['nsecode']}: {e}")

        #progress.progress((idx + 1) / len(chartink_data))

    #st.success(f"📨 Total Telegram alerts sent: {alert_count}")
else:
    st.warning("⚠️ No results from Chartink screener.")

st.title("📊 bullish momentum stocks")
with st.spinner("📥 Fetching Screener Results..."):
    url = "https://chartink.com/screener/process"
    condition = {
        "scan_clause": "( {33489} ( latest close > latest ema( latest close , 20 ) and latest close > latest ema( latest close , 50 ) and latest rsi( 14 ) > 50 and latest close <= greatest(  latest high, 1 day ago high, 2 days ago high, 3 days ago high, 4 days ago high, 5 days ago high, 6 days ago high, 7 days ago high, 8 days ago high, 9 days ago high, 10 days ago high, 11 days ago high, 12 days ago high, 13 days ago high, 14 days ago high, 15 days ago high, 16 days ago high, 17 days ago high, 18 days ago high, 19 days ago high  ) * 1.03 and latest close >= least(  latest low, 1 day ago low, 2 days ago low, 3 days ago low, 4 days ago low, 5 days ago low, 6 days ago low, 7 days ago low, 8 days ago low, 9 days ago low, 10 days ago low, 11 days ago low, 12 days ago low, 13 days ago low, 14 days ago low, 15 days ago low, 16 days ago low, 17 days ago low, 18 days ago low, 19 days ago low  ) * 0.97 and( 14 ) < latest sma( latest volume , 14 ) and latest close > 100 and latest volume >= 200000 and( {166311} not( latest close > 0 ) ) and (latest close - 1 candle ago close / 1 candle ago close * 100) >= 0 ) ) "
    }
    
  

    try:
        with requests.Session() as s:
            r = s.get(url)
            soup = bs(r.content, "lxml")
            meta = soup.find("meta", {"name": "csrf-token"})["content"]
            headers = {"x-csrf-token": meta}
            response = s.post(url, headers=headers, data=condition)
            chartink_data = pd.DataFrame(response.json()["data"])
    except Exception as e:
        st.error(f"Chartink Fetch Error: {e}")
        st.stop()

# --- PROCESS AND SEND ALERTS ---
if not chartink_data.empty:
    st.success(f"✅ Fetched {len(chartink_data)} results.")
    st.dataframe(chartink_data)



   # st.subheader("📬 Sending Telegram Alerts")
   # alert_count = 0
   # progress = st.progress(0)

    for idx, row in chartink_data.iterrows():
        try:
           # print("hi"+row['nsecode'])
            time.sleep(1)
            search = smartApi.searchScrip("NSE", row['nsecode'] + "-EQ")
            
            if search.get("data"):
                for stock in search['data']:
                    token = stock.get("symboltoken")
                    symbol = stock.get("symbol", row["nsecode"])

                    if not token:
                        st.warning(f"⚠️ Token not found for {row['nsecode']}")
                        continue

                    mktdata = smartApi.getMarketData("FULL", {"NSE": [token]})

                    if mktdata["data"].get("fetched"):
                        d = mktdata["data"]["fetched"][0]
                        ltp = d.get("ltp")
                        high = d.get("high")
                        open_ = d.get("open")
                        low = d.get("low")

                        if None in (ltp, high, open_, low):
                            st.warning(f"⚠️ Incomplete data for {symbol}")
                            continue

                        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        gap = round(high - ltp, 2)
                        if ltp > low and gap > 10:
                            message = (
                                f"*📢 Stock Alert: {symbol}*\n\n"
                                f"🗓 Date: {date_str}\n"
                                f"▶️ LTP: ₹{ltp}\n"
                                f"📈 High: ₹{high}\n"
                                f"🟢 Open: ₹{open_}\n"
                                f"📉 Low: ₹{low}\n"
                                f"🔍 Gap: ₹{gap}"
                            )
                          #  resp = send_telegram_message(message)
                           # if resp and resp.status_code == 200:
                            #    alert_count += 1
                           # else:
                            #    st.error(f"❌ Telegram failed: {resp.status_code if resp else 'Unknown error'}")
            else:
                st.warning(f"⚠️ No data found for {row['nsecode']}")
        except Exception as e:
            st.warning(f"❗ Error processing {row['nsecode']}: {e}")

       # progress.progress((idx + 1) / len(chartink_data))

    #st.success(f"📨 Total Telegram alerts sent: {alert_count}")
else:
    st.warning("⚠️ No results from Chartink screener.")    
