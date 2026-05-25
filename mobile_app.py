import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

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
            return {
                "last": float(data.get("last", 0))    # 只保留最新成交價
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
    
    # 回歸最安全、100% 不會被幣安拒絕的基礎 Payload
    payload = {
        "fiat": "VND", 
        "page": 1, 
        "rows": 5, 
        "tradeType": trade_type,
        "asset": "USDT", 
        "countries": [], 
        "payTypes": [],            # 保持留空，避免觸發後端字串阻擋
        "proMerchantAds": False, 
        "shieldMerchantAds": False, 
        "publisherType": None      # 保持留空，確保能成功拿到數據
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("data"):
                # 提取前幾筆商家的價格
                prices = [float(item["adv"]["price"]) for item in res_json["data"]]
                
                if len(prices) >= 2:
                    if trade_type == "BUY":
                        # BUY (用戶買入)：正常常規排序應由低到高 (如 26417, 26419)
                        # 如果第一筆（置頂廣告）大於第二筆（如 27329 > 26417），說明是高價廣告，自動跳過並精準鎖定第二排常規報價！
                        if prices[0] > prices[1]:
                            return prices[1]
                        return prices[0]
                    else:
                        # SELL (用戶賣出)：正常常規排序應由高到低 (如 26400, 26380)
                        # 如果第一筆小於第二筆，說明是低價廣告，自動跳過取第二排常規報價！
                        if prices[0] < prices[1]:
                            return prices[1]
                        return prices[0]
                elif len(prices) == 1:
                    return prices[0]
    except:
        pass
    return None

# 🔄 立即確認最新價格按鈕
st.button("🔄 立即確認最新價格", use_container_width=True)

# 獲取即時數據
max_data = get_max_usdt_twd()
vnd_buy = get_binance_p2p_usdt_vnd("BUY")
vnd_sell = get_binance_p2p_usdt_vnd("SELL")

# 強制修正為台灣時區 (UTC+8)
taiwan_tz = timezone(timedelta(hours=8))
now = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
st.write(f"🕒 台灣報價時間：`{now}`")

st.markdown("---")

# 顯示台灣 MAX 交易所區塊
st.subheader("🇹🇼 台灣 MAX 交易所 (USDT/TWD)")
if max_data:
    st.metric(label="最新成交價 (TWD)", value=f"{max_data['last']:.3f}")
else:
    st.error("MAX 數據獲取失敗")

st.markdown("---")

# 顯示幣安 P2P 越南盾區塊
st.subheader("🇻🇳 幣安 P2P 越南盾 (USDT/VND)")
if vnd_buy and vnd_sell:
    col1, col2 = st.columns(2)
    col1.metric(label="VND 買 USDT (真實市場最優成本)", value=f"{vnd_buy:,.0f} ₫")
    col2.metric(label="USDT 換 VND (變現)", value=f"{vnd_sell:,.0f} ₫")
else:
    st.error("幣安 P2P 數據獲取失敗")
