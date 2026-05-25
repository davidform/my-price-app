import streamlit as st
import requests
from datetime import datetime

# 設定網頁標題與手機版優化
st.set_page_config(page_title="跨境匯率監控", page_icon="💰", layout="centered")

st.title("💰 跨境資產即時報價")
st.caption("專為手機設計的即時監控面板")

def get_max_usdt_twd():
    url = "https://max-api.maicoin.com/api/v2/tickers/usdttwd"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"buy": float(data.get("buy", 0)), "sell": float(data.get("sell", 0))}
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
        "fiat": "VND", "page": 1, "rows": 1, "tradeType": trade_type,
        "asset": "USDT", "countries": [], "payTypes": [],
        "proMerchantAds": False, "shieldMerchantAds": False, "publisherType": None
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("data"):
                return float(res_json["data"][0]["adv"]["price"])
    except:
        pass
    return None

# 手動刷新按鈕
if st.button("🔄 立即刷新最新價格", use_container_width=True):
    st.rerun()

# 獲取即時數據
max_data = get_max_usdt_twd()
vnd_buy = get_binance_p2p_usdt_vnd("BUY")
vnd_sell = get_binance_p2p_usdt_vnd("SELL")

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"🕒 報價時間：`{now}`")

st.markdown("---")

# 顯示台灣 MAX 交易所區塊
st.subheader("🇹🇼 台灣 MAX 交易所 (USDT/TWD)")
if max_data:
    col1, col2 = st.columns(2)
    col1.metric(label="用戶買入價 (TWD)", value=f"{max_data['buy']:.2f}")
    col2.metric(label="用戶賣出價 (TWD)", value=f"{max_data['sell']:.2f}")
else:
    st.error("MAX 數據獲取失敗")

st.markdown("---")

# 顯示幣安 P2P 越南盾區塊
st.subheader("🇻🇳 幣安 P2P 越南盾 (USDT/VND)")
if vnd_buy and vnd_sell:
    col3, col4 = st.columns(2)
    col3.metric(label="VND 買 USDT (成本)", value=f"{vnd_buy:,.0f} ₫")
    col4.metric(label="USDT 換 VND (變現)", value=f"{vnd_sell:,.0f} ₫")
else:
    st.error("幣安 P2P 數據獲取失敗")