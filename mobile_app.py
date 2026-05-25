import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# 設定網頁標題與手機版優化
st.set_page_config(page_title="即時報價", page_icon="💰", layout="centered")

# 🔒 網頁唯讀安全防護：全面禁止文字選取與複製
st.markdown(
    """
    <style>
    body, [data-testid="stAppViewContainer"], [data-testid="stMetricValue"] {
        -webkit-user-select: none; /* Safari */
        -moz-user-select: none;    /* Firefox */
        -ms-user-select: none;     /* IE10+ */
        user-select: none;         /* Standard */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 1. 修改主標題
st.title("即時報價")
st.caption("專為手機設計的即時監控面板")

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
                
                # 自動識別並剔除付費置頂廣告
                if len(valid_prices) >= 2:
                    if trade_type == "BUY":
                        if valid_prices[0] > valid_prices[1]:
                            return valid_prices[1]
                        return valid_prices[0]
                elif len(valid_prices) == 1:
                    return valid_prices[0]
    except:
        pass
    return None

# 🔄 立即確認最新價格按鈕
st.button("🔄 立即確認最新價格", use_container_width=True)

# 獲取即時數據 (已移除不必要的 SELL 數據請求，優化載入速度)
max_data = get_max_usdt_twd()
vnd_buy = get_binance_p2p_usdt_vnd("BUY")

# 強制修正為台灣時區 (UTC+8)
taiwan_tz = timezone(timedelta(hours=8))
now = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
st.write(f"🕒 台灣報價時間：`{now}`")

st.markdown("---")

# 2. 修改為指定的 MAX 區塊名稱
st.subheader("MAX (USDT/TWD)")
if max_data:
    st.metric(label="最新成交價 (TWD)", value=f"{max_data['last']:.3f}")
else:
    st.error("MAX 數據獲取失敗")

st.markdown("---")

# 3. 修改為指定的 Binance P2P 區塊名稱
st.subheader("VND/USDT (Binance P2P)")
if vnd_buy:
    # 4. 已完全刪除原有的賣出 (變現) 資訊，只保留單一純淨的買入報價大字卡
    st.metric(label="VND 買 USDT (真實市場最優成本)", value=f"{vnd_buy:,.0f} ₫")
else:
    st.error("幣安 P2P 數據獲取失敗")
