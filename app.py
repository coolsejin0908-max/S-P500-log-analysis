# ------------------------------
# 4. 변동성 집중 시기 + 히트맵 (완전 수정 - 안전한 처리)
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
    top_months = pd.Series(dtype=float)  # 빈 시리즈

# 히트맵: 연도-월 평균 로그수익률
st.write("**월별 평균 로그수익률 히트맵**")
mean_returns = log_returns.mean(axis=1).dropna()

if len(mean_returns) >= 2:  # 최소 2개 이상의 데이터 포인트 필요
    # 데이터 준비
    heatmap_df = pd.DataFrame({
        'year': mean_returns.index.year,
        'month': mean_returns.index.month,
        'return': mean_returns.values
    })
    # 피벗 테이블 생성
    heatmap_data = heatmap_df.pivot(index='year', columns='month', values='return')
    
    # 컬럼명을 숫자로 유지 (px.imshow는 문자열 컬럼도 처리 가능하지만 혹시 몰라 숫자로)
    # 하지만 x축 레이블을 월로 표시하려면 나중에 update_xaxes로 처리 가능
    # 일단 숫자로 유지
    if heatmap_data.empty:
        st.warning("⚠️ 피벗 테이블이 비어 있습니다.")
    else:
        # 모든 값을 float로 강제 변환 (문자열이 섞였을 경우 대비)
        heatmap_data = heatmap_data.astype(float)
        
        # NaN이 너무 많은 경우 경고
        if heatmap_data.isnull().all().all():
            st.warning("⚠️ 모든 값이 NaN입니다. 더 긴 기간을 선택하세요.")
        else:
            # 그래프 생성
            try:
                fig_heat = px.imshow(
                    heatmap_data,
                    text_auto='.2f',
                    aspect='auto',
                    color_continuous_scale='RdBu_r',
                    title='월별 평균 로그수익률 (%)',
                    template='plotly_dark',
                    zmid=0,
                    origin='upper'  # 명시적으로 지정
                )
                # x축을 월 숫자에서 '1월' ~ '12월'로 변경
                fig_heat.update_xaxes(tickvals=list(range(len(heatmap_data.columns))),
                                      ticktext=[f'{int(m)}월' for m in heatmap_data.columns])
                fig_heat.update_layout(height=500)
                st.plotly_chart(fig_heat, use_container_width=True)
            except Exception as e:
                st.error(f"히트맵 생성 중 오류 발생: {e}")
                st.write("원본 데이터 미리보기:")
                st.dataframe(heatmap_data)
else:
    st.info("📊 히트맵을 표시할 충분한 수익률 데이터가 없습니다. (최소 2개 이상의 월 데이터 필요)")

st.markdown('</div>', unsafe_allow_html=True)
