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
    page_title="로그 변동성 분석 | 기술주 vs 소비재주",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# 커스텀 CSS (다크 모드)
# ------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    .css-1d391kg, .css-12oz5g0 {
        background-color: #1a1c23;
    }
    .custom-card {
        background-color: #1e2128;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #2c2f36;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .stButton > button {
        background-color: #2c6e9e;
        color: white;
        border-radius: 24px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        border: none;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #1e4e72;
        transform: scale(1.02);
    }
    .dataframe {
        background-color: #1e2128;
        color: #f0f2f6;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# 헤더 이미지
# ------------------------------
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://images.unsplash.com/photo-1611974789855-9c56a4c81e6a?w=100&auto=format", width=80)
with col_title:
    st.title("📈 로그 변동성 분석")
    st.markdown("**기술주 vs 소비재주** – 상용로그 기반 월별 변동성 비교")

st.markdown("---")

# ------------------------------
# 사이드바 설정
# ------------------------------
st.sidebar.header("🔧 분석 설정")
st.sidebar.markdown("### 핵심 질문")
st.sidebar.info("기술주와 소비재주의 월별 변동성 차이와 집중 시기는?")

tech_stocks = st.sidebar.multiselect(
    "📱 기술주 선택",
    ["NVDA", "AAPL", "MSFT", "GOOGL", "META"],
    default=["NVDA", "AAPL"]
)

consumer_stocks = st.sidebar.multiselect(
    "🛒 소비재주 선택",
    ["KO", "PG", "PEP", "COST", "WMT"],
    default=["KO", "PG"]
)

start_date = st.sidebar.date_input("📅 시작일", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("📅 종료일", datetime(2024, 12, 31))

run_analysis = st.sidebar.button("🚀 분석 시작", type="primary", use_container_width=True)

# ------------------------------
# 데이터 로드 함수
# ------------------------------
@st.cache_data
def load_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end, group_by='ticker', auto_adjust=False)
    if len(tickers) == 1:
        return pd.DataFrame({tickers[0]: data['Close']})
    else:
        return data.xs('Close', axis=1, level=1)

# ------------------------------
# 분석 실행
# ------------------------------
if run_analysis:
    if not tech_stocks and not consumer_stocks:
        st.warning("⚠️ 최소 하나의 종목을 선택해주세요.")
        st.stop()

    all_stocks = tech_stocks + consumer_stocks

    with st.spinner("📡 주가 데이터를 불러오는 중입니다..."):
        try:
            price_data = load_data(all_stocks, start_date, end_date)
            monthly_price = price_data.resample('ME').last()
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            st.stop()

    # 상용로그 변환
    log_price = np.log10(monthly_price)
    log_returns = log_price.diff() * 100  # 월별 로그 수익률(%)

    # ------------------------------
    # 1. 데이터 미리보기
    # ------------------------------
    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("🔢 1. 상용로그 변환 결과")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**원본 종가 (USD)**")
            st.dataframe(monthly_price.tail(8), use_container_width=True)
        with col2:
            st.markdown("**log₁₀(가격)**")
            st.dataframe(log_price.tail(8), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 2. 시계열 차트 (Plotly)
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📉 2. 시계열 비교")
    
    fig = make_subplots(rows=2, cols=2, subplot_titles=("원본 종가", "로그 가격 (log₁₀)", "월별 로그 수익률 (%)", "12개월 롤링 변동성"))
    
    for col in monthly_price.columns:
        fig.add_trace(go.Scatter(x=monthly_price.index, y=monthly_price[col], name=col, mode='lines'), row=1, col=1)
    for col in log_price.columns:
        fig.add_trace(go.Scatter(x=log_price.index, y=log_price[col], name=col, mode='lines', showlegend=False), row=1, col=2)
    for col in log_returns.columns:
        fig.add_trace(go.Scatter(x=log_returns.index, y=log_returns[col], name=col, mode='lines'), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="red", row=2, col=1)
    rolling_vol = log_returns.rolling(12).std()
    for col in rolling_vol.columns:
        fig.add_trace(go.Scatter(x=rolling_vol.index, y=rolling_vol[col], name=col, mode='lines'), row=2, col=2)
    
    fig.update_layout(height=700, template="plotly_dark", showlegend=True)
    fig.update_xaxes(title_text="날짜", row=1, col=1)
    fig.update_xaxes(title_text="날짜", row=1, col=2)
    fig.update_yaxes(title_text="가격 (USD)", row=1, col=1)
    fig.update_yaxes(title_text="log₁₀(가격)", row=1, col=2)
    fig.update_yaxes(title_text="수익률 (%)", row=2, col=1)
    fig.update_yaxes(title_text="변동성 (%)", row=2, col=2)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 3. 변동성 분포 박스플롯
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📊 3. 기술주 vs 소비재주 변동성 분포")
    
    vol_df = pd.DataFrame()
    for s in tech_stocks:
        if s in log_returns.columns:
            vol_df[f"{s} (기술)"] = log_returns[s].dropna()
    for s in consumer_stocks:
        if s in log_returns.columns:
            vol_df[f"{s} (소비)"] = log_returns[s].dropna()
    
    vol_melt = vol_df.melt(var_name="종목", value_name="로그 수익률 (%)")
    fig_box = px.box(vol_melt, x="종목", y="로그 수익률 (%)", color="종목",
                     title="월별 로그 수익률 분포",
                     template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2)
    fig_box.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_box, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 4. 변동성 집중 시기 + 히트맵 (수정됨)
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("⏰ 4. 변동성 집중 시기")
    
    abs_returns = log_returns.abs().mean(axis=1).dropna()
    top_months = abs_returns.nlargest(5)
    st.write("**전체 종목 평균 절대 로그수익률 TOP5**")
    st.dataframe(top_months.reset_index().rename(columns={"index": "날짜", 0: "평균 |로그수익률| (%)"}), use_container_width=True)
    
    # 히트맵: 연도별-월별 평균 로그수익률
    st.write("**월별 평균 로그수익률 히트맵**")
    mean_returns = log_returns.mean(axis=1).dropna()
    # 날짜를 연도와 월로 분리하여 피벗 테이블 생성
    heatmap_df = pd.DataFrame({
        'year': mean_returns.index.year,
        'month': mean_returns.index.month,
        'return': mean_returns.values
    })
    heatmap_data = heatmap_df.pivot(index='year', columns='month', values='return')
    # 월 컬럼 이름을 1~12에서 '1월'~'12월'로 변경 (선택사항)
    heatmap_data.columns = [f"{int(col)}월" for col in heatmap_data.columns]
    
    fig_heat = px.imshow(heatmap_data, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r",
                         title="월별 평균 로그수익률 (%)", template="plotly_dark", zmid=0)
    fig_heat.update_layout(height=500)
    st.plotly_chart(fig_heat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------
    # 5. 결과 요약
    # ------------------------------
    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("💡 탐구 결과 요약")
        tech_vol = log_returns[tech_stocks].std().mean() if tech_stocks else 0
        cons_vol = log_returns[consumer_stocks].std().mean() if consumer_stocks else 0
        peak_month = top_months.index[0].strftime('%Y년 %m월') if not top_months.empty else "없음"
        
        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            st.metric("📱 기술주 평균 월별 변동성", f"{tech_vol:.2f}%", delta="높음" if tech_vol > cons_vol else "낮음")
            st.metric("🛒 소비재주 평균 월별 변동성", f"{cons_vol:.2f}%")
        with col_sum2:
            st.markdown(f"**🔥 가장 큰 변동이 있었던 달:** {peak_month}")
            st.markdown("**🔍 상용로그의 역할**  \n주가를 log₁₀ 변환하면 지수 성장이 선형이 되어 상대적 변화율(수익률)을 직관적으로 비교할 수 있습니다.")
        st.markdown(f"**예상과 일치?** 기술주의 변동성이 소비재주보다 {abs(tech_vol - cons_vol):.2f}%p 더 큽니다.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("👈 왼쪽 사이드바에서 종목과 기간을 선택한 후 **분석 시작** 버튼을 눌러주세요.")
    col_img1, col_img2, col_img3 = st.columns(3)
    with col_img2:
        st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=400&auto=format", 
                 caption="시장 데이터를 로그 관점으로 분석해보세요", use_container_width=True)
