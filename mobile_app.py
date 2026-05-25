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
    
    # 嚴格對齊網頁版篩選條件
    payload = {
        "fiat": "VND", 
        "page": 1, 
        "rows": 5, 
        "tradeType": trade_type,
        "asset": "USDT", 
        "countries": [], 
        "payTypes": ["BankTransfer"],  # ✨ 只鎖定越南銀行轉帳，過濾奇特電子錢包的異常匯率
        "proMerchantAds": False, 
        "shieldMerchantAds": False, 
        "publisherType": "merchant"    # ✨ 只看認證商家廣告，完全與網頁版勾選「顯示商家廣告」同步
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("data"):
                # 依序提取前幾筆合格商家的價格
                prices = [float(item["adv"]["price"]) for item in res_json["data"]]
                
                if len(prices) >= 2:
                    if trade_type == "BUY":
                        # 用戶買入（找低價）：常規排序應由低到高（如 26417, 26419, 26425）
                        # 如果第一筆(置頂廣告)價格反而比第二筆高，說明它是高價廣告，直接抓取第二個常規報價
                        if prices[0] > prices[1]:
                            return prices[1]
                        return prices[0]
                    else:
                        # 用戶賣出（找高價）：常規排序應由高到低（如 26400, 26380, 26350）
                        # 如果第一筆(置頂廣告)價格反而比第二筆低，說明它是低價廣告，直接抓取第二個常規報價
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
