import streamlit as st
import pandas as pd
import feedparser
from nsepython import nse_eq
from streamlit_autorefresh import st_autorefresh
from concurrent.futures import ThreadPoolExecutor

# CONFIG
st.set_page_config(layout="wide")
st_autorefresh(interval=2 * 60 * 1000, key="refresh")  # Auto-refresh every 2 minutes

# Sidebar filter
st.sidebar.markdown("### 📂 News Settings")
filter_term = st.sidebar.text_input("Filter by sector or stock (e.g. BANK, RELIANCE):").strip()

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
st.dataframe(perf_df.style.applymap(color_change, subset=["Avg Change (%)"]), use_container_width=True, height=280)

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

