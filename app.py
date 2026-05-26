import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date
import platform

# ... (한글 폰트 설정, 페이지 설정, CSS는 동일) ...

# ------------------------------
# 사이드바 설정 (날짜 제한 없음)
# ------------------------------
st.sidebar.header("🔧 분석 설정")
tech_stocks = st.sidebar.multiselect("📱 기술주 선택", ["NVDA","AAPL","MSFT","GOOGL","META"], default=["NVDA","AAPL"])
consumer_stocks = st.sidebar.multiselect("🛒 소비재주 선택", ["KO","PG","PEP","COST","WMT"], default=["KO","PG"])

# ✅ 날짜 선택에 max_value 제거 (미래 날짜도 선택 가능)
start_date = st.sidebar.date_input("📅 시작일", date(2020,1,1))
end_date = st.sidebar.date_input("📅 종료일", date(2024,12,31))

run_analysis = st.sidebar.button("🚀 분석 시작", type="primary")

# ------------------------------
# 분석 실행
# ------------------------------
if run_analysis:
    today = date.today()
    
    # 날짜 검증 및 자동 보정
    if start_date > today:
        st.error(f"❌ 시작일({start_date})은 오늘({today}) 이후일 수 없습니다. 데이터가 존재하지 않습니다.")
        st.stop()
    if end_date > today:
        st.warning(f"⚠️ 종료일이 오늘 이후로 설정되어 ({end_date}) → 오늘({today})로 변경합니다. 미래 데이터는 없습니다.")
        end_date = today
    if end_date < start_date:
        st.error("❌ 종료일이 시작일보다 빠를 수 없습니다.")
        st.stop()
    if not tech_stocks and not consumer_stocks:
        st.warning("⚠️ 최소 하나의 종목을 선택하세요.")
        st.stop()
    
    # ... (이후 데이터 로드, 분석, 시각화는 동일) ...
    
    # 데이터 로드 시 start_date, end_date 사용 (end_date는 오늘로 조정됨)
    price_data = load_data(all_stocks, start_date, end_date)
    
    if price_data.empty:
        st.warning(f"📭 선택한 기간({start_date} ~ {end_date})에 해당하는 데이터가 없습니다. 더 이른 시작일을 선택하세요.")
        st.stop()
    
    # ... (나머지 코드는 이전과 동일) ...
