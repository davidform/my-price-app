import streamlit as st
import requests
import threading
import telebot
import os
from datetime import datetime, timedelta, timezone

# 1. 網頁端初始化與視覺控制
st.set_page_config(page_title="即時報價", page_icon="💰", layout="centered")

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
    
    /* 核心控距 */
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

st.markdown("<h1 style='text-align: center;'>即時報價</h1>", unsafe_allow_html=True)

# 2. 核心數據抓取邏輯 (全面升級為官方 iOS App 智慧防護通道)
def get_max_usdt_twd():
    url = "https://max-api.maicoin.com/api/v2/tickers/usdttwd"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"last": float(data.get("last", 0))}
    except:
        pass
    return None

def get_binance_p2p_usdt_vnd(trade_type="BUY"):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # 🕵️‍♂️ 終極偽裝：全面模擬官方手機 App 標頭，避開網頁端的常規審查
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Binance/2.83.0",
        "Clienttype": "ios",
        "Lang": "zh-TW"
    }
    
    # 將 rows 修正為安全合理的 30 筆，不觸發大數據採集警報
    payload = {
        "asset": "USDT",
        "fiat": "VND",
        "page": 1,
        "rows": 30,
        "tradeType": trade_type,
        "payTypes": []
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=6)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("data") and len(res_json["data"]) > 0:
                valid_prices = []   # 優先池：黃勾認證商家 + 銀行轉帳
                backup_prices = []  # 備用池：常規商家 + 銀行轉帳
                
                for item in res_json["data"]:
                    is_merchant = item.get("advertiser", {}).get("userType") == "merchant"
                    trade_methods = item.get("adv", {}).get("tradeMethods", [])
                    has_bank = False
                    for method in trade_methods:
                        m_name = str(method.get("tradeMethodName", "")).lower()
                        m_id = str(method.get("identifier", "")).lower()
                        if "bank" in m_name or "transfer" in m_name or "bank" in m_id:
                            has_bank = True
                            break
                    
                    if has_bank:
                        if is_merchant:
                            valid_prices.append(float(item["adv"]["price"]))
                        else:
                            backup_prices.append(float(item["adv"]["price"]))
                
                # 智慧權重決策
                final_pool = valid_prices if valid_prices else backup_prices
                
                if len(final_pool) >= 2:
                    if trade_type == "BUY":
                        return (final_pool[1] if final_pool[0] > final_pool[1] else final_pool[0]), "OK"
                    else:
                        return (final_pool[1] if final_pool[0] < final_pool[1] else final_pool[0]), "OK"
                elif len(final_pool) == 1:
                    return final_pool[0], "OK"
                return None, "未篩選到支援銀行轉帳的商家"
            return None, "幣安回傳空數據池"
        else:
            return None, f"HTTP {response.status_code}"
    except Exception as e:
        return None, f"連線超時: {str(e)}"

# 3. 🤖 Telegram 機器人背景智慧執行緒
@st.cache_resource
def launch_telegram_bot():
    try:
        tg_token = os.environ.get("TELEGRAM_TOKEN")
        if not tg_token and "TELEGRAM_TOKEN" in st.secrets:
            tg_token = st.secrets["TELEGRAM_TOKEN"]
            
        if not tg_token:
            return

        bot = telebot.TeleBot(tg_token)

        @bot.message_handler(func=lambda message: True)
        def reply_current_prices(message):
            max_data = get_max_usdt_twd()
            vnd_buy, buy_err = get_binance_p2p_usdt_vnd("BUY")
            vnd_sell, sell_err = get_binance_p2p_usdt_vnd("SELL")
            
            taiwan_tz = timezone(timedelta(hours=8))
            timestamp = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            reply_text = f"📊 即時報價單\n"
            reply_text += f"Update Time: {timestamp}\n"
            reply_text += f"────────────────\n"
            if max_data:
                reply_text += f"🔸 MAX (USDT/TWD) : {max_data['last']:.3f}\n"
            if vnd_buy and vnd_sell:
                reply_text += f"🔸 VND/USDT : {vnd_buy:,.0f} ₫\n"
                reply_text += f"🔸 USDT/VND : {vnd_sell:,.0f} ₫\n"
            else:
                reply_text += f"❌ 幣安 P2P 異常\n"
            reply_text += f"────────────────"
            bot.reply_to(message, reply_text)

        threading.Thread(target=bot.infinity_polling, daemon=True).start()
    except:
        pass

# 啟動機器人
launch_telegram_bot()

# 4. 網頁端前端畫面渲染
st.button("更新價格", use_container_width=True)

max_data = get_max_usdt_twd()
vnd_buy, buy_msg = get_binance_p2p_usdt_vnd("BUY")
vnd_sell, sell_msg = get_binance_p2p_usdt_vnd("SELL")

taiwan_tz = timezone(timedelta(hours=8))
now = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
st.write(f"Update Time: `{now}`")

st.markdown("---")
st.subheader("MAX")
if max_data:
    st.metric(label="USDT / TWD", value=f"{max_data['last']:.3f}")
else:
    st.error("MAX 數據獲取失敗")

st.markdown("---")
st.subheader("Binance P2P")
if vnd_buy and vnd_sell:
    col1, col2 = st.columns(2)
    col1.metric(label="VND / USDT", value=f"{vnd_buy:,.0f} ₫")
    col2.metric(label="USDT / VND", value=f"{vnd_sell:,.0f} ₫")
else:
    st.error(f"❌ 幣安 P2P 數據獲取失敗（原因：{buy_msg if vnd_buy is None else sell_msg}）")
