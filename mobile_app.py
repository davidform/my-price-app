import streamlit as st
import requests
import time
from datetime import datetime, timedelta, timezone

# 設定網頁標題與手機版優化
st.set_page_config(page_title="即時報價", page_icon="💰", layout="centered")

# 🔒 終極視覺控制：全面禁止複製、標題置中、大幅縮減上下行距與元件間隙
st.markdown(
    """
    <style>
    body, [data-testid="stAppViewContainer"], [data-testid="stMetricValue"] {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    [data-testid="stVerticalBlock"] > div {
        padding-top: 0rem !important;
        padding-bottom: 0.2rem !important;
    }
    .stMetric { margin-top: -12px !important; }
    hr { margin-top: 8px !important; margin-bottom: 8px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# 標題絕對置中
st.markdown("<h1 style='text-align: center;'>即時報價</h1>", unsafe_allow_html=True)

# 💾 初始化記憶骨幹 (Session State)，確保斷線時畫面不崩潰
if "last_max_price" not in st.session_state:
    st.session_state.last_max_price = 31.500  # 預設初始值
if "last_vnd_buy" not in st.session_state:
    st.session_state.last_vnd_buy = 26400.0
if "last_vnd_sell" not in st.session_state:
    st.session_state.last_vnd_sell = 26400.0
if "status_msg" not in st.session_state:
    st.session_state.status_msg = ""

def get_max_usdt_twd_safe():
    url = "https://max-api.maicoin.com/api/v2/tickers/usdttwd"
    # 🔄 自動重試機制：失敗時自動重試 3 次
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=4)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get("last", 0))
                if price > 0:
                    st.session_state.last_max_price = price  # 成功則更新記憶
                    return price
        except:
            time.sleep(0.5) # 失敗後微調等待再重試
    return st.session_state.last_max_price # 3次皆失敗則調用歷史記憶

def get_binance_p2p_safe(trade_type="BUY"):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0"
    }
    # 擴大 rows 至 50 筆，確保極端市況下仍有充足數據供 Python 過濾
    payload = {
        "fiat": "VND", "page": 1, "rows": 50, "tradeType": trade_type,
        "asset": "USDT", "countries": [], "payTypes": [],
        "proMerchantAds": False, "shieldMerchantAds": False, "publisherType": None
    }
    
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=4)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("data"):
                    valid_prices = []
                    for item in res_json["data"]:
                        # 嚴格過濾：認證商家
                        is_merchant = item.get("advertiser", {}).get("userType") == "merchant"
                        # 嚴格過濾：銀行轉帳
                        trade_methods = item.get("adv", {}).get("tradeMethods", [])
                        has_bank = False
                        for method in trade_methods:
                            m_name = str(method.get("tradeMethodName", "")).lower()
                            m_id = str(method.get("identifier", "")).lower()
                            if "bank" in m_name or "transfer" in m_name or "bank" in m_id:
                                has_bank = True
                                break
                        
                        if is_merchant and has_bank:
                            valid_prices.append(float(item["adv"]["price"]))
                    
                    # 廣告剔除演算法
                    if len(valid_prices) >= 2:
                        if trade_type == "BUY":
                            final_price = valid_prices[1] if valid_prices[0] > valid_prices[1] else valid_prices[0]
                        else:
                            final_price = valid_prices[1] if valid_prices[0] < valid_prices[1] else valid_prices[0]
                        
                        if trade_type == "BUY":
                            st.session_state.last_vnd_buy = final_price
                        else:
                            st.session_state.last_vnd_sell = final_price
                        return final_price
                    elif len(valid_prices) == 1:
                        if trade_type == "BUY":
                            st.session_state.last_vnd_buy = valid_prices[0]
                        else:
                            st.session_state.last_vnd_sell = valid_prices[0]
                        return valid_prices[0]
        except:
            time.sleep(0.5)
            
    # 若全面失敗，回傳歷史記憶
    return st.session_state.last_vnd_buy if trade_type == "BUY" else st.session_state.last_vnd_sell

# 更新價格按鈕
st.button("更新價格", use_container_width=True)

# 執行安全抓取 (系統會自動處理重試與記憶回傳)
max_price = get_max_usdt_twd_safe()
vnd_buy = get_binance_p2p_safe("BUY")
vnd_sell = get_binance_p2p_safe("SELL")

# 時間時區設定
taiwan_tz = timezone(timedelta(hours=8))
now = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
st.write(f"Update Time: `{now}`")

st.markdown("---")

# MAX 交易所區塊展示
st.subheader("MAX (USDT/TWD)")
st.metric(label="最新成交價 (TWD)", value=f"{max_price:.3f}")

st.markdown("---")

# 幣安 P2P 區塊展示
st.subheader("VND/USDT (Binance P2P)")
col1, col2 = st.columns(2)
col1.metric(label="VND 買 USDT", value=f"{vnd_buy:,.0f} ₫")
col2.metric(label="USDT 買 VND", value=f"{vnd_sell:,.0f} ₫")
