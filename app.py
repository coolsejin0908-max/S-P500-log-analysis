```python
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ------------------------------
# 페이지 설정
# ------------------------------
st.set_page_config(
    page_title="로그 변동성 분석",
    page_icon="📈",
    layout="wide"
)

# ------------------------------
# CSS
# ------------------------------
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}

.custom-card {
    background-color: #1e2128;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 제목
# ------------------------------
st.title("📈 로그 변동성 분석")
st.markdown("기술주 vs 소비재주 월별 로그 변동성 비교")

# ------------------------------
# 사이드바
# ------------------------------
st.sidebar.header("분석 설정")

tech_stocks = st.sidebar.multiselect(
    "기술주 선택",
    ["NVDA", "AAPL", "MSFT", "GOOGL", "META"],
    default=["NVDA", "AAPL"]
)

consumer_stocks = st.sidebar.multiselect(
    "소비재주 선택",
    ["KO", "PG", "PEP", "WMT", "COST"],
    default=["KO", "PG"]
)

start_date = st.sidebar.date_input(
    "시작일",
    datetime(2020, 1, 1)
)

end_date = st.sidebar.date_input(
    "종료일",
    datetime(2024, 12, 31)
)

run_analysis = st.sidebar.button("🚀 분석 시작")

# ------------------------------
# 데이터 로드 함수
# ------------------------------
@st.cache_data
def load_data(tickers, start, end):

    data = yf.download(
        tickers,
        start=start,
        end=end,
        group_by='ticker',
        auto_adjust=False
    )

    if len(tickers) == 1:
        return pd.DataFrame({
            tickers[0]: data['Close']
        })

    return data.xs('Close', axis=1, level=1)

# ------------------------------
# 분석 시작
# ------------------------------
if run_analysis:

    if not tech_stocks and not consumer_stocks:
        st.warning("최소 1개 종목 선택 필요")
        st.stop()

    all_stocks = tech_stocks + consumer_stocks

    # ------------------------------
    # 데이터 다운로드
    # ------------------------------
    with st.spinner("데이터 불러오는 중..."):

        try:
            price_data = load_data(
                all_stocks,
                start_date,
                end_date
            )

            monthly_price = price_data.resample('ME').last()

        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            st.stop()

    # ------------------------------
    # 로그 변환
    # ------------------------------
    log_price = np.log10(monthly_price)

    # 로그 수익률
    log_returns = log_price.diff() * 100

    # ------------------------------
    # 1. 데이터 보기
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    st.subheader("🔢 1. 로그 변환 결과")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 원본 종가")
        st.dataframe(monthly_price.tail())

    with col2:
        st.markdown("### log₁₀ 가격")
        st.dataframe(log_price.tail())

    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 2. 시계열 그래프
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    st.subheader("📉 2. 시계열 비교")

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "원본 종가",
            "로그 가격",
            "로그 수익률",
            "롤링 변동성"
        )
    )

    # 원본 가격
    for col in monthly_price.columns:
        fig.add_trace(
            go.Scatter(
                x=monthly_price.index,
                y=monthly_price[col],
                mode='lines',
                name=col
            ),
            row=1,
            col=1
        )

    # 로그 가격
    for col in log_price.columns:
        fig.add_trace(
            go.Scatter(
                x=log_price.index,
                y=log_price[col],
                mode='lines',
                showlegend=False
            ),
            row=1,
            col=2
        )

    # 로그 수익률
    for col in log_returns.columns:
        fig.add_trace(
            go.Scatter(
                x=log_returns.index,
                y=log_returns[col],
                mode='lines',
                name=col
            ),
            row=2,
            col=1
        )

    # 롤링 변동성
    rolling_vol = log_returns.rolling(12).std()

    for col in rolling_vol.columns:
        fig.add_trace(
            go.Scatter(
                x=rolling_vol.index,
                y=rolling_vol[col],
                mode='lines',
                showlegend=False
            ),
            row=2,
            col=2
        )

    fig.update_layout(
        height=700,
        template="plotly_dark"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 3. 박스플롯
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    st.subheader("📊 3. 변동성 분포")

    vol_df = pd.DataFrame()

    for s in tech_stocks:
        if s in log_returns.columns:
            vol_df[f"{s} (기술)"] = log_returns[s]

    for s in consumer_stocks:
        if s in log_returns.columns:
            vol_df[f"{s} (소비)"] = log_returns[s]

    vol_melt = vol_df.melt(
        var_name="종목",
        value_name="로그 수익률"
    )

    fig_box = px.box(
        vol_melt,
        x="종목",
        y="로그 수익률",
        color="종목",
        template="plotly_dark"
    )

    st.plotly_chart(
        fig_box,
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 4. 변동성 집중 시기
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    st.subheader("⏰ 4. 변동성 집중 시기")

    abs_returns = log_returns.abs().mean(axis=1).dropna()

    top_months = abs_returns.nlargest(5)

    st.write("### 평균 절대 로그수익률 TOP5")

    top_df = top_months.reset_index()
    top_df.columns = ["날짜", "평균 절대 로그수익률"]

    st.dataframe(top_df)

    # ------------------------------
    # 히트맵
    # ------------------------------
    st.write("### 월별 평균 로그수익률 히트맵")

    mean_returns = log_returns.mean(axis=1).dropna()

    heatmap_df = pd.DataFrame({
        "연도": mean_returns.index.year,
        "월": mean_returns.index.month,
        "수익률": mean_returns.values
    })

    heatmap_data = heatmap_df.pivot(
        index="연도",
        columns="월",
        values="수익률"
    )

    heatmap_data = heatmap_data.astype(float)

    month_labels = [
        "1월", "2월", "3월", "4월",
        "5월", "6월", "7월", "8월",
        "9월", "10월", "11월", "12월"
    ]

    heatmap_data.columns = [
        month_labels[col - 1]
        for col in heatmap_data.columns
    ]

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale="RdBu",
            zmid=0,
            text=np.round(
                heatmap_data.values,
                2
            ),
            texttemplate="%{text}"
        )
    )

    fig_heat.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig_heat,
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 5. 결과 요약
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    st.subheader("💡 결과 요약")

    tech_vol = 0
    cons_vol = 0

    if tech_stocks:
        tech_vol = log_returns[tech_stocks].std().mean()

    if consumer_stocks:
        cons_vol = log_returns[consumer_stocks].std().mean()

    peak_month = top_months.index[0].strftime('%Y-%m')

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "기술주 평균 변동성",
            f"{tech_vol:.2f}%"
        )

        st.metric(
            "소비재주 평균 변동성",
            f"{cons_vol:.2f}%"
        )

    with col2:

        st.markdown(
            f"### 🔥 최대 변동 시기\n{peak_month}"
        )

        st.markdown("""
상용로그를 사용하면  
상대적인 변화율을 더 직관적으로 비교할 수 있습니다.
""")

    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# 시작 화면
# ------------------------------
else:

    st.info("왼쪽 사이드바에서 설정 후 분석 시작 버튼 클릭")

```
