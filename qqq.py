
import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# تحميل رموز ناسداك
nasdaq_url = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed.csv"
response = requests.get(nasdaq_url)
lines = response.text.splitlines()
symbols = [line.split(',')[0] for line in lines[1:] if line.split(',')[0].isalpha()]
section_size = 500
num_sections = (len(symbols) + section_size - 1) // section_size

# واجهة المستخدم
st.title("🧠 فلتر الأسهم حسب DCF و هامش FCF")
section = st.selectbox("📦 اختر القسم:", [f"القسم {i+1}" for i in range(num_sections)])
growth_type = st.radio("📈 نوع النمو:", ["نمو مبسط", "نمو مركب"])
timeframe = st.radio("🕓 الفترة:", ["سنوي", "ربع سنوي"])
min_margin = st.number_input("📊 هامش FCF الأدنى (CFC):", min_value=0.0, max_value=100.0, value=25.0)
multiplier = st.number_input("💰 المضاعف للسعر العادل:", min_value=0.5, max_value=10.0, value=2.0)
run_filter = st.button("🔍 ابدأ الفحص")

def calculate_dcf(fcf, shares, simplified=True, years=10, growth=0.15, discount=0.11, terminal_growth=0.04):
    if simplified:
        return (fcf / shares) * 10
    else:
        fcf_per_share = fcf / shares
        dcf_value = 0
        for year in range(1, years + 1):
            future_fcf = fcf_per_share * ((1 + growth) ** year)
            discounted_fcf = future_fcf / ((1 + discount) ** year)
            dcf_value += discounted_fcf
        terminal_value = (future_fcf * (1 + terminal_growth)) / (discount - terminal_growth)
        dcf_value += terminal_value / ((1 + discount) ** years)
        return dcf_value

if run_filter:
    section_index = int(section.split()[-1]) - 1
    simplified = growth_type == "نمو مبسط"
    selected_symbols = symbols[section_index * section_size : (section_index + 1) * section_size]

    results = []
    with st.spinner("⏳ جاري الفحص..."):
        for i, symbol in enumerate(selected_symbols):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                fcf = info.get("freeCashflow")
                shares = info.get("sharesOutstanding")
                price = info.get("currentPrice")
                revenue = info.get("totalRevenue")
                if fcf and shares and price and revenue:
                    dcf = calculate_dcf(fcf, shares, simplified=simplified)
                    fcf_margin = (fcf / revenue) * 100
                    passed = dcf >= price * multiplier and fcf_margin >= min_margin
                    if passed:
                        results.append({
                            "رمز السهم": symbol,
                            "السعر الحالي": round(price, 2),
                            "هامش FCF": f"{fcf_margin:.2f}%",
                            "السعر العادل": round(dcf, 2)
                        })
            except:
                continue

    if results:
        df = pd.DataFrame(results)
        st.success(f"✅ عدد الأسهم التي اجتازت الفلترة: {len(df)} من أصل {len(selected_symbols)}")
        st.dataframe(df)
    else:
        st.error("❌ لا توجد أسهم اجتازت الفلترة.")
