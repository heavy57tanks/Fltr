# -*- coding: utf-8 -*-
"""Flter.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Aiz4T1m3M1mvskDes2fuGtFoV6HegcCZ
"""


import yfinance as yf
import pandas as pd

import requests

# نحمل رموز ناسداك من ملف جاهز
nasdaq_url = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed.csv"
response = requests.get(nasdaq_url)

# نحول الملف لقائمة رموز
lines = response.text.splitlines()
symbols = [line.split(',')[0] for line in lines[1:]]

print(f"عدد الأسهم في ناسداك: {len(symbols)}")
symbols[:10]  # نطبع أول 10 رموز للتأكد

import yfinance as yf
import pandas as pd
import requests
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import time

# تحميل رموز ناسداك
nasdaq_url = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed.csv"
response = requests.get(nasdaq_url)
lines = response.text.splitlines()
symbols = [line.split(',')[0] for line in lines[1:] if line.split(',')[0].isalpha()]
print(f"عدد الأسهم في ناسداك: {len(symbols)}")

section_size = 500
num_sections = (len(symbols) + section_size - 1) // section_size

# عناصر الواجهة
section_dropdown = widgets.Dropdown(
    options=[f'القسم {i+1}' for i in range(num_sections)],
    description='📦 القسم:',
    style={'description_width': 'initial'},
)

growth_type = widgets.ToggleButtons(
    options=['نمو مبسط', 'نمو مركب'],
    description='📈 نوع النمو:',
    style={'description_width': 'initial'},
)

timeframe_type = widgets.ToggleButtons(
    options=['سنوي', 'ربع سنوي'],
    description='🕓   الفترة:',
    style={'description_width': 'initial'},
)

margin_input = widgets.BoundedFloatText(
    value=25.0,
    min=0,
    max=100,
    step=1,
    description='📊 CFC:',
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='200px')
)

multiplier_input = widgets.BoundedFloatText(
    value=2.0,
    min=0.5,
    max=10,
    step=0.1,
    description='💰 العادل:',
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='200px')
)

start_button = widgets.Button(description='🔍 ابدأ الفحص', button_style='success')
results_button = widgets.Button(description='📁 عرض آخر النتائج', button_style='info')

progress = widgets.IntProgress(value=0, min=0, max=100, layout=widgets.Layout(width='60%'))
progress_label = widgets.Label("0%", layout=widgets.Layout(width='50px'))

output = widgets.Output()
summary_label = widgets.HTML()

all_results = {}

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

def get_key(section, growth, timeframe):
    return f"{section} | {growth} | {timeframe}"

def on_start_clicked(b):
    output.clear_output()
    with output:
        start_button.description = "⏳ جاري الفحص..."
        start_button.disabled = True
        progress.value = 0
        progress_label.value = "0%"

        section_index = int(section_dropdown.value.split()[-1]) - 1
        simplified = growth_type.value == 'نمو مبسط'
        timeframe = timeframe_type.value
        min_margin = margin_input.value
        multiplier = multiplier_input.value

        key = get_key(section_dropdown.value, growth_type.value, timeframe)
        start = section_index * section_size
        end = start + section_size
        selected_symbols = symbols[start:end]

        passed_count = 0
        results_this_run = []

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
                    if symbol not in all_results:
                        all_results[symbol] = {
                            "السعر الحالي": round(price, 2),
                            "سنوي مبسط": None,
                            "سنوي مركب": None,
                            "ربع سنوي مبسط": None,
                            "ربع سنوي مركب": None,
                        }
                    label_type = f"{timeframe} {'مبسط' if simplified else 'مركب'}"
                    label_value = round(dcf, 2)
                    if passed:
                        passed_count += 1
                        all_results[symbol][label_type] = ("✔️", label_value)
                        results_this_run.append((symbol, round(price, 2), round(fcf_margin, 2), label_value))
                    else:
                        all_results[symbol][label_type] = ("❌", label_value)
            except:
                continue

            if i % 5 == 0:
                progress.value = int((i + 1) / len(selected_symbols) * 100)
                progress_label.value = f"{progress.value}%"

        summary_label.value = f"""
        ✅ تم فحص <b>{len(selected_symbols)}</b> سهم.<br>
        ✅ عدد الأسهم التي اجتازت الفلترة: <b>{passed_count}</b>
        """

        if results_this_run:
            rows = []
            for sym, price, margin, fair_value in results_this_run:
                rows.append({
                    "رمز السهم": sym,
                    "السعر الحالي": price,
                    "هامش FCF": f"{margin:.2f}%",
                    "السعر العادل": fair_value
                })
            df = pd.DataFrame(rows)
            html = df.to_html(escape=False, index=False)
            display(HTML(html))
        else:
            print("❌ لا توجد أسهم اجتازت الفلترة.")

        start_button.description = "🔍 ابدأ الفحص"
        start_button.disabled = False

def on_show_results(b):
    output.clear_output()
    with output:
        rows = []
        for symbol, data in all_results.items():
            has_check = any(v is not None and v[0] == "✔️" for k, v in data.items() if k != "السعر الحالي")
            if has_check:
                row = {
                    "رمز السهم": symbol,
                    "السعر الحالي": data["السعر الحالي"]
                }
                for col in ["سنوي مركب", "سنوي مبسط", "ربع سنوي مركب", "ربع سنوي مبسط"]:
                    if data[col] is None:
                        row[col] = f'<span style="color:gray">—</span>'
                    else:
                        status, value = data[col]
                        color = "green" if status == "✔️" else "red"
                        row[col] = f'<span style="color:{color}">{value}</span>'
                rows.append(row)

        if not rows:
            print("❌ لا توجد نتائج ناجحة لعرضها.")
            return

        df = pd.DataFrame(rows)
        html = df.to_html(escape=False, index=False)
        display(HTML(html))

start_button.on_click(on_start_clicked)
results_button.on_click(on_show_results)

# عرض الواجهة
ui = widgets.VBox([
    section_dropdown,
    growth_type,
    timeframe_type,
    widgets.HBox([margin_input, multiplier_input]),
    widgets.HBox([start_button, results_button]),
    widgets.HBox([progress, progress_label]),
    summary_label,
    output
])

display(ui)
