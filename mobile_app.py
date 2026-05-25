import streamlit as st
import requests
import threading
import telebot
from datetime import datetime, timedelta, timezone

# 1. 網頁端初始化與視覺控制
st.set_page_config(page_title="即時報價", page_icon="💰", layout="centered")

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

st.markdown("<h1 style='text-align: center;'>即時報價</h1>", unsafe_allow_html=True)

# 2. 數據抓取核心邏輯
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
                    is_merchant = item.get("advertiser", {}).get("userType") == "merchant"
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
                
                if len(valid_prices) >= 2:
                    if trade_type == "BUY":
                        return valid_prices[1] if valid_prices[0] > valid_prices[1] else valid_prices[0]
                    else:
                        return valid_prices[1] if valid_prices[0] < valid_prices[1] else valid_prices[0]
                elif len(valid_prices) == 1:
                    return valid_prices[0]
    except:
        pass
    return None

# 3. 🤖 Telegram 機器人背景智慧監聽（內建自我診斷防線）
@st.cache_resource
def launch_telegram_bot():
    status = {"success": True, "error_msg": ""}
    try:
        # 檢查保險箱是否存在金鑰
        if "TELEGRAM_TOKEN" not in st.secrets:
            status["success"] = False
            status["error_msg"] = "Streamlit Secrets 保險箱內找不到 'TELEGRAM_TOKEN' 設定，請檢查設定是否正確儲存。"
            return status

        tg_token = st.secrets["TELEGRAM_TOKEN"]
        bot = telebot.TeleBot(tg_token)

        @bot.message_handler(func=lambda message: True)
        def reply_current_prices(message):
            max_data = get_max_usdt_twd()
            vnd_buy = get_binance_p2p_usdt_vnd("BUY")
            vnd_sell = get_binance_p2p_usdt_vnd("SELL")
            
            taiwan_tz = timezone(timedelta(hours=8))
            timestamp = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            reply_text = f"📊 即時報價單\n"
            reply_text += f"Update Time: {timestamp}\n"
            reply_text += f"────────────────\n"
            if max_data:
                reply_text += f"緊鄰市場：\n"
                reply_text += f"🔸 MAX (USDT/TWD) 最新成交: {max_data['last']:.3f}\n\n"
            if vnd_buy and vnd_sell:
                reply_text += f"跨境市場：\n"
                reply_text += f"🔸 VND 買 USDT: {vnd_buy:,.0f} ₫\n"
                reply_text += f"🔸 USDT 買 VND: {vnd_sell:,.0f} ₫\n"
            reply_text += f"────────────────"
            bot.reply_to(message, reply_text)

        # 啟動長輪詢監聽
        threading.Thread(target=bot.infinity_polling, daemon=True).start()
    except Exception as e:
        status["success"] = False
        status["error_msg"] = f"機器人連線時發生未預期崩潰: {str(e)}"
    return status

# 呼叫診斷器
bot_status = launch_telegram_bot()

# 若機器人啟動失敗，直接大大的呈現在網頁上提示你
if not bot_status["success"]:
    st.error(f"❌ Telegram 機器人未成功啟動！\n原因：{bot_status['error_msg']}")

# 4. 網頁端前端畫面渲染
st.button("更新價格", use_container_width=True)

max_data = get_max_usdt_twd()
vnd_buy = get_binance_p2p_usdt_vnd("BUY")
vnd_sell = get_binance_p2p_usdt_vnd("SELL")

taiwan_tz = timezone(timedelta(hours=8))
now = datetime.now(taiwan_tz).strftime("%Y-%m-%d %H:%M:%S")
st.write(f"Update Time: `{now}`")

st.markdown("---")
st.subheader("MAX (USDT/TWD)")
if max_data:
    st.metric(label="最新成交價 (TWD)", value=f"{max_data['last']:.3f}")
else:
    st.error("MAX 數據獲取失敗")

st.markdown("---")
st.subheader("VND/USDT (Binance P2P)")
if vnd_buy and vnd_sell:
    col1, col2 = st.columns(2)
    col1.metric(label="VND 買 USDT", value=f"{vnd_buy:,.0f} ₫")
    col2.metric(label="USDT 買 VND", value=f"{vnd_sell:,.0f} ₫")
else:
    st.error("幣安 P2P 數據獲取失敗")
