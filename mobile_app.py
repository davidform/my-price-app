import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# 設定網頁標題與手機版優化
st.set_page_config(page_title="即時報價", page_icon="💰", layout="centered")

# 🔒 終極視覺控制：全面禁止複製、標題置中、大幅縮減上下行距與元件間隙
st.markdown(
    """
    <style>
    /* 禁止文字選取與複製 */
    body, [data-testid="stAppViewContainer"], [data-testid="stMetricValue"] {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    
    /* 核心控距：大幅拉近所有元件的上下行距 */
    [data-testid="stVerticalBlock"] > div {
        padding-top: 0rem !important;
        padding-bottom: 0.2rem !important;
    }
    
    /* 縮減數據字卡 (Metric) 的上方空白 */
    .stMetric {
        margin-top: -12px !important;
    }
    
    /* 縮減分隔線的上下外級距 */
    hr {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 標題完全置中（副標題已徹底移除）
st.markdown("<h1 style='text-align: center;'>即時報價</h1>", unsafe_allow_html=True)

def get_max_usdt_twd():
    url = "https://max-api.maicoin.com/api/v2/tickers/usdttwd"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "last": float(data.get("last", 0))
            }
    except:
        pass
    return None

def get_binance_p2p_usdt_vnd(trade_type="BUY"):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "fiat": "VND", "page": 1, "rows": 20, "tradeType": trade_type,
        "asset": "USDT", "countries": [], "payTypes": [],
        "proMerchantAds": False, "shieldMerchantAds": False, "publisherType": None
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("data"):
                valid_prices = []
                for item in res_json["data"]:
                    # 篩選認證商家
                    is_merchant = item.get("advertiser", {}).get("userType") == "merchant"
                    
                    # 篩選銀行轉帳
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
                
                # ✨ 自動識別並剔除付費置頂廣告，精準鎖定第二個常規欄位報價
                if len(valid_prices) >= 2:
                    if trade_type == "BUY":
                        # 購買（找低價）：若第一筆大於第二筆，說明是置頂廣告，自動跳過取第二個常規最優價
                        if valid_prices[0] > valid_prices[1]:
                            return valid_prices[1]
                        return valid_prices[0]
                    else:
                        # 出售（找高價）：若第一筆小於第二筆，說明是置頂廣告，自動跳過取第二個常規最優價
                        if valid_prices[0] < valid_prices[1]:
                            return valid_prices[1]
                        return valid_prices[0]
                elif len(valid_prices) == 1:
                    return valid_prices[0]
    except:
        pass
    return None

# 更新價格按鈕（無圖示）
st.button("更新價格", use_container_width=True)

# 同時獲取 BUY 與 SELL 的即時數據
max_data = get_max_usdt_twd()
vnd_buy = get_binance_p2p_usdt_vnd("BUY")
vnd_sell = get_binance_p2p_usdt_vnd("SELL")

# 強制修正為台灣時區 (UTC+8)
taiwan_tz = timezone(timedelta(hours=8))
now = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")

# 修改為指定的英文時間標籤（無圖示）
st.write(f"Update Time: `{now}`")

st.markdown("---")

# MAX 交易所區塊
st.subheader("MAX (USDT/TWD)")
if max_data:
    st.metric(label="最新成交價 (TWD)", value=f"{max_data['last']:.3f}")
else:
    st.error("MAX 數據獲取失敗")

st.markdown("---")

# 幣安 P2P 區塊
st.subheader("VND/USDT (Binance P2P)")
if vnd_buy and vnd_sell:
    col1, col2 = st.columns(2)
    # 左欄：VND 買 USDT 的最優常規報價
    col1.metric(label="VND 買 USDT", value=f"{vnd_buy:,.0f} ₫")
    # 右欄：USDT 買 VND（即出售 tab）的最優常規報價
    col2.metric(label="USDT 買 VND", value=f"{vnd_sell:,.0f} ₫")
else:
    st.error("幣安 P2P 數據獲取失敗")
