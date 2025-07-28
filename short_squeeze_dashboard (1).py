
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Short Squeeze Dashboard", layout="wide")
st.title("📈 Short Squeeze Opportunity Dashboard")

@st.cache_data(ttl=3600)
def get_finviz_data():
    url = "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=sh_short_o30"  # Stocks with short float >30%
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find_all("table", class_="table-light")[1]
    rows = table.find_all("tr")[1:]

    tickers = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 1:
            ticker = cols[1].text.strip()
            tickers.append(ticker)
    return tickers[:20]  # Limit to top 20

@st.cache_data(ttl=3600)
def fetch_metrics(tickers):
    data = []
    for ticker in tickers:
        try:
            url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            tables = soup.find_all("table")
            metrics = {"Ticker": ticker}

            for table in tables:
                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) == 2:
                        label = cells[0].text.strip()
                        value = cells[1].text.strip()
                        if label == "Short % of Float":
                            metrics["Short Float"] = value
                        elif label == "Shares Short (prior month)":
                            metrics["Shares Short"] = value
                        elif label == "Float":
                            metrics["Float"] = value

            if "Short Float" in metrics and "%" in metrics["Short Float"]:
                score = float(metrics["Short Float"].replace("%", ""))
                metrics["Signal Score"] = score
            else:
                metrics["Signal Score"] = 0

            data.append(metrics)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    df = pd.DataFrame(data)
    if "Signal Score" in df.columns:
        df = df.sort_values("Signal Score", ascending=False)
    else:
        st.warning("⚠️ No 'Signal Score' column found. Data may be incomplete.")
        st.write(df)
    return df

tickers = get_finviz_data()
st.sidebar.markdown("## Filters")
min_short_float = st.sidebar.slider("Minimum Short % Float", 0, 100, 30)

results_df = fetch_metrics(tickers)
filtered_df = results_df[results_df["Signal Score"] >= min_short_float]

st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
