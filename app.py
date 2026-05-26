import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import platform

# ------------------------------
# 한글 폰트 설정 (matplotlib/seaborn)
# ------------------------------
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':  # Mac
    plt.rcParams['font.family'] = 'AppleGothic'
else:  # Linux (Streamlit Cloud)
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

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
# 사이드바 설정 (날짜 제한 + 종목 선택)
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

# ✅ 오늘 날짜를 최대값으로 설정
today = date.today()
start_date = st.sidebar.date_input(
    "📅 시작일",
    date(2020, 1, 1),
    max_value=today
)
end_date = st.sidebar.date_input(
    "📅 종료일",
    date(2024, 12, 31),
    max_value=today
)

run_analysis = st.sidebar.button("🚀 분석 시작", type="primary", use_container_width=True)

# ------------------------------
# 데이터 로드 함수 (수정됨)
# ------------------------------
@st.cache_data
def load_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end, group_by='ticker', auto_adjust=False)
    if len(tickers) == 1:
        df = pd.DataFrame({tickers[0]: data['Close']})
    else:
        df = data.xs('Close', axis=1, level=1)
    
    # 모든 값이 NaN인 컬럼 제거
    df = df.dropna(axis=1, how='all')
    # 결측치 앞뒤로 채우기
    df = df.ffill().bfill()
    return df

# ------------------------------
# 분석 실행
# ------------------------------
if run_analysis:
    # ===================== 날짜 유효성 검증 =====================
    if end_date < start_date:
        st.error("❌ 종료일이 시작일보다 빠를 수 없습니다.")
        st.stop()
    if end_date > today:
        st.error(f"❌ 종료일은 오늘({today.strftime('%Y-%m-%d')}) 이전이어야 합니다.")
        st.stop()
    
    # 최소 분석 기간: 30일 (1개월) 미만은 경고 후 중단
    min_days = 30
    if (end_date - start_date).days < min_days:
        st.warning(f"⚠️ 선택한 기간이 {min_days}일 미만입니다. 의미 있는 변동성을 보려면 더 긴 기간을 선택하세요.")
        st.stop()
    
    if not tech_stocks and not consumer_stocks:
        st.warning("⚠️ 최소 하나의 종목을 선택해주세요.")
        st.stop()
    
    all_stocks = tech_stocks + consumer_stocks
    
    # (선택사항) 너무 많은 종목 방지
    if len(all_stocks) > 10:
        st.warning("⚠️ 종목이 10개를 초과하면 데이터 로드가 지연될 수 있습니다. 일부 종목만 선택해주세요.")
        # 여기서 멈추지 않고 진행 (경고만)
    
    with st.spinner("📡 주가 데이터를 불러오는 중입니다..."):
        try:
            price_data = load_data(all_stocks, start_date, end_date)
            
            if price_data.empty:
                st.error("선택한 종목의 데이터가 없습니다. 다른 종목이나 기간을 선택하세요.")
                st.stop()
            
            monthly_price = price_data.resample('ME').last()
            monthly_price = monthly_price.ffill().bfill()
            
            # 0 이하 값 확인
            if (monthly_price <= 0).any().any():
                st.warning("일부 종목에 0 이하 가격이 있어 로그 변환 시 문제가 발생할 수 있습니다.")
                
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            st.stop()
    
    # 상용로그 변환
    log_price = np.log10(monthly_price.clip(lower=1e-6))
    log_returns = log_price.diff() * 100
    
    # ===================== 12개월 롤링 변동성을 위한 데이터 충분성 검사 =====================
    insufficient_rolling = False
    if len(log_returns) < 12:
        st.warning(f"📊 12개월 롤링 변동성을 표시하려면 최소 12개월의 데이터가 필요합니다. (현재 {len(log_returns)}개월)")
        insufficient_rolling = True
    
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
    
    if not insufficient_rolling:
        rolling_vol = log_returns.rolling(12).std()
        for col in rolling_vol.columns:
            fig.add_trace(go.Scatter(x=rolling_vol.index, y=rolling_vol[col], name=col, mode='lines'), row=2, col=2)
    else:
        # 데이터 부족 시 빈 플롯에 메시지 표시
        fig.add_annotation(text="데이터 부족 (12개월 미만)", xref="x2 domain", yref="y2 domain",
                           x=0.5, y=0.5, showarrow=False, row=2, col=2)
    
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
    
    if vol_df.empty:
        st.warning("선택한 종목의 수익률 데이터가 없습니다.")
    else:
        vol_melt = vol_df.melt(var_name="종목", value_name="로그 수익률 (%)")
        fig_box = px.box(vol_melt, x="종목", y="로그 수익률 (%)", color="종목",
                         title="월별 로그 수익률 분포",
                         template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_box.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_box, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ------------------------------
    # 4. 변동성 집중 시기 + 히트맵
    # ------------------------------
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("⏰ 4. 변동성 집중 시기")
    
    abs_returns = log_returns.abs().mean(axis=1).dropna()
    if not abs_returns.empty:
        top_months = abs_returns.nlargest(5)
        st.write("**전체 종목 평균 절대 로그수익률 TOP5**")
        st.dataframe(top_months.reset_index().rename(columns={"index": "날짜", 0: "평균 |로그수익률| (%)"}), use_container_width=True)
    else:
        st.info("충분한 수익률 데이터가 없어 TOP5를 표시할 수 없습니다.")
    
    st.write("**월별 평균 로그수익률 히트맵**")
    mean_returns = log_returns.mean(axis=1).dropna()
    
    if len(mean_returns) >= 2:
        heatmap_df = pd.DataFrame({
            'year': mean_returns.index.year,
            'month': mean_returns.index.month,
            'return': mean_returns.values
        })
        heatmap_data = heatmap_df.pivot(index='year', columns='month', values='return')
        
        if not heatmap_data.empty and not heatmap_data.isnull().all().all():
            heatmap_data = heatmap_data.fillna(0).astype(float)
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=[f"{int(m)}월" for m in heatmap_data.columns],
                y=heatmap_data.index,
                colorscale='RdBu_r',
                zmid=0,
                text=heatmap_data.values.round(2),
                texttemplate='%{text:.2f}',
                textfont={"size": 10}
            ))
            fig_heat.update_layout(
                title="월별 평균 로그수익률 (%)",
                xaxis_title="월",
                yaxis_title="연도",
                template="plotly_dark",
                height=500
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.warning("⚠️ 히트맵 데이터가 모두 비어 있습니다. 더 긴 기간을 선택하세요.")
    else:
        st.info("📊 히트맵을 표시할 충분한 데이터가 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ------------------------------
    # 5. 결과 요약
    # ------------------------------
    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("💡 탐구 결과 요약")
        if tech_stocks:
            tech_vol = log_returns[tech_stocks].std().mean()
        else:
            tech_vol = 0
        if consumer_stocks:
            cons_vol = log_returns[consumer_stocks].std().mean()
        else:
            cons_vol = 0
        
        peak_month = "없음"
        if 'top_months' in locals() and not top_months.empty:
            peak_month = top_months.index[0].strftime('%Y년 %m월')
        
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
