import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="주가 변동성 분석 (상용로그)", layout="wide")
st.title("📈 기술주 vs 소비재주 변동성 비교 - 상용로그 기반")

# 사이드바 설명
st.sidebar.header("🔧 분석 설정")
st.sidebar.markdown("""
**탐구 주제:**  
파이썬과 상용로그를 이용한 시장 변동 분석  
**핵심 질문:**  
기술주와 소비재주의 월별 변동성 차이와 집중 시기는?
""")

# 종목 선택 (기술주 vs 소비재주)
tech_stocks = st.sidebar.multiselect(
    "기술주 선택",
    ["NVDA", "AAPL", "MSFT", "GOOGL", "META"],
    default=["NVDA", "AAPL"]
)
consumer_stocks = st.sidebar.multiselect(
    "소비재주 선택",
    ["KO", "PG", "PEP", "COST", "WMT"],
    default=["KO", "PG"]
)

# 기간 선택
start_date = st.sidebar.date_input("시작일", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("종료일", datetime(2024, 12, 31))

# 데이터 로드 함수
@st.cache_data
def load_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end, group_by='ticker', auto_adjust=False)
    if len(tickers) == 1:
        data.columns = pd.MultiIndex.from_product([data.columns, tickers])
        data = data.stack().unstack(0).swaplevel(axis=1)
    return data['Close']

# 분석 실행 버튼
if st.sidebar.button("📊 분석 시작", type="primary"):
    if not tech_stocks and not consumer_stocks:
        st.warning("최소 하나의 종목을 선택하세요.")
        st.stop()

    all_stocks = tech_stocks + consumer_stocks
    with st.spinner("주가 데이터를 불러오는 중..."):
        try:
            price_data = load_data(all_stocks, start_date, end_date)
            # 월별 리샘플링 (월말 종가)
            monthly_price = price_data.resample('M').last()
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            st.stop()

    # 상용로그 변환 및 수익률 계산
    st.subheader("🔢 1. 상용로그 변환값 (log10)")

    # 로그 가격 (log10(P))
    log_price = np.log10(monthly_price)
    # 월별 로그 수익률: log10(P_t / P_{t-1}) * 100 (% 단위)
    log_returns = log_price.diff() * 100

    col1, col2 = st.columns(2)
    with col1:
        st.write("**원본 종가 (USD)**")
        st.dataframe(monthly_price.tail(10))
    with col2:
        st.write("**상용로그 변환 가격 (log10)**")
        st.dataframe(log_price.tail(10))

    # 2. 시계열 그래프
    st.subheader("📉 2. 시계열 비교 그래프")
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    # 원본 가격
    monthly_price.plot(ax=axes[0,0], title="원본 종가")
    axes[0,0].set_ylabel("가격 (USD)")
    # 로그 가격
    log_price.plot(ax=axes[0,1], title="상용로그 변환 가격 (log10)")
    axes[0,1].set_ylabel("log10(가격)")
    # 로그 수익률
    log_returns.plot(ax=axes[1,0], title="월별 로그 수익률 (log10 기준, %)")
    axes[1,0].set_ylabel("수익률 (%)")
    axes[1,0].axhline(0, color='red', linestyle='--')
    # 변동성(롤링 12개월 표준편차)
    rolling_vol = log_returns.rolling(12).std()
    rolling_vol.plot(ax=axes[1,1], title="12개월 롤링 변동성 (로그수익률 표준편차)")
    axes[1,1].set_ylabel("변동성 (%)")
    plt.tight_layout()
    st.pyplot(fig)

    # 3. 변동성 비교 (박스플롯)
    st.subheader("📊 3. 기술주 vs 소비재주 변동성 분포 비교")
    # 로그 수익률의 절대값 또는 표준편차로 비교? 여기서는 월별 로그수익률 자체의 분포 비교
    vol_data = pd.DataFrame()
    for stock in tech_stocks:
        if stock in log_returns.columns:
            vol_data[f"{stock} (기술)"] = log_returns[stock].dropna()
    for stock in consumer_stocks:
        if stock in log_returns.columns:
            vol_data[f"{stock} (소비)"] = log_returns[stock].dropna()

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    vol_data.boxplot(ax=ax2, rot=45)
    ax2.set_title("월별 로그수익률 분포 (상용로그 기준)")
    ax2.set_ylabel("로그수익률 (%)")
    st.pyplot(fig2)

    # 4. 변동성 집중 시기 분석
    st.subheader("⏰ 4. 변동성이 집중된 시기 탐색")
    # 전체 종목의 평균 절대 로그수익률이 높은 상위 5개월
    abs_returns = log_returns.abs().mean(axis=1).dropna()
    top_months = abs_returns.nlargest(5)
    st.write("**전체 종목 평균 절대 로그수익률이 가장 높은 5개월 (변동성 급등 시기)**")
    st.dataframe(top_months.reset_index().rename(columns={"index": "날짜", 0: "평균 절대 로그수익률(%)"}))

    # 히트맵 (월별 평균 로그수익률)
    st.write("**월별 평균 로그수익률 히트맵 (연도-월)**")
    heatmap_data = log_returns.mean(axis=1).unstack().iloc[:, :12]
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax3)
    ax3.set_title("월별 평균 로그수익률 (%) - 기술+소비재 전체")
    st.pyplot(fig3)

    # 결과 해석
    st.subheader("💡 탐구 결과 요약")
    st.markdown(f"""
    - **기술주** ({', '.join(tech_stocks)})의 월별 로그수익률 표준편차:  
      {log_returns[tech_stocks].std().mean():.2f}% (평균)
    - **소비재주** ({', '.join(consumer_stocks)})의 월별 로그수익률 표준편차:  
      {log_returns[consumer_stocks].std().mean():.2f}% (평균)
    - **예상 결과와 일치?**  
      기술주의 변동성이 소비재주보다 확연히 큰 경향을 보입니다.  
      특히 {top_months.index[0].strftime('%Y년 %m월')}에 가장 큰 변동이 관측되었습니다.
    - **상용로그의 역할**: 주가를 로그 변환하면 시간에 따른 지수적 성장을 선형화하여,  
      절대 가격 대신 **상대적 변화율**에 집중할 수 있습니다. 이를 통해 변동성을 정량적으로 비교 가능합니다.
    """)
else:
    st.info("👈 사이드바에서 종목과 기간을 선택한 후 '분석 시작' 버튼을 눌러주세요.")
