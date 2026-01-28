# views.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re

# 모듈 임포트
import config
from config import COLOR_NAVY, COLOR_RED, COLOR_GREY, CHART_PALETTE, COLOR_GENDER
from utils import WEEK_MAP
from datetime import datetime, timedelta
import data

# ----------------- 차트 생성 헬퍼 함수 -----------------
def create_donut_chart_with_val(df, names, values, color_map=None, height=350, margin=None, rotation=90, show_legend=False, limit_labels=None):
    if df.empty: return go.Figure()
    final_margin = margin if margin else dict(t=30, b=80, l=40, r=40)
    
    if '구분' in df.columns and len(df) == 1 and df['구분'].iloc[0] == '기타':
        fig = go.Figure(data=[go.Pie(
            labels=['기타 100%'],
            values=[df[values].iloc[0]],
            hole=0.5,
            marker=dict(colors=[COLOR_GREY]),
            textinfo='label',
            textposition='outside',
            rotation=rotation
        )])
        fig.update_layout(showlegend=False, margin=final_margin, height=height)
        return fig
    
    if '구분' in df.columns:
        df_normal = df[df['구분'] != '기타'].sort_values(by=values, ascending=False)
        df_other = df[df['구분'] == '기타']
        df_sorted = pd.concat([df_normal, df_other])
    else: df_sorted = df

    if color_map: 
        fig = px.pie(df_sorted, names=names, values=values, hole=0.5, color=names, color_discrete_map=color_map)
    else: 
        fig = px.pie(df_sorted, names=names, values=values, hole=0.5, color_discrete_sequence=CHART_PALETTE)
    
    if limit_labels:
        total_val = df_sorted[values].sum()
        custom_text = []
        for i in range(len(df_sorted)):
            if i < limit_labels:
                row_val = df_sorted.iloc[i][values]
                row_name = df_sorted.iloc[i][names]
                pct = (row_val / total_val * 100) if total_val > 0 else 0
                custom_text.append(f"{row_name} {pct:.1f}%")
            else:
                custom_text.append("")
        fig.update_traces(text=custom_text, textinfo='text', textposition='outside', sort=False, rotation=rotation, automargin=True)
    else:
        fig.update_traces(textposition='outside', textinfo='label+percent', sort=False, rotation=rotation, automargin=True)
    
    layout_update = dict(showlegend=show_legend, margin=final_margin, height=height)
    if show_legend:
        layout_update['legend'] = dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
    fig.update_layout(**layout_update)
    return fig

# ----------------- 1. 성과 요약 -----------------
def render_summary(df_weekly, cur_pv, cur_uv, new_ratio, search_ratio, df_daily, active_article_count, published_article_count=0):
    st.markdown('<div class="section-header-container first-section"><div class="section-header">1. 주간 전체 성과 요약</div></div>', unsafe_allow_html=True)
    pv_per_user = round(cur_pv/cur_uv, 1) if cur_uv > 0 else 0
    
    kpis = [
        ("활성 기사 수", active_article_count, "건"),
        ("발행 기사 수", published_article_count, "건"),
        ("지난 7일 간<br>조회수(PV)", cur_pv, "건"),
        ("지난 7일 간<br>방문자수(UV)", cur_uv, "명"), 
        ("방문자당 페이지뷰", pv_per_user, "건"),
        ("신규 방문자 비율", new_ratio, "%"),
        ("검색 유입 비율", search_ratio, "%")
    ]
    
    cols = st.columns(7)
    for i, (l, v, u) in enumerate(kpis):
        v_f = f"{v:,}" if isinstance(v, (int, np.integer, float)) and l not in ["방문자당 페이지뷰", "신규 방문자 비율", "검색 유입 비율"] else str(v)
        cols[i].markdown(f'<div class="kpi-container"><div class="kpi-label">{l}</div><div class="kpi-value">{v_f}<span class="kpi-unit">{u}</span></div></div>', unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sub-header">📊 주간 일별 방문 추이</div>', unsafe_allow_html=True)
        if not df_daily.empty:
            df_melted = df_daily.melt(id_vars='날짜')
            fig = px.bar(df_melted, x='날짜', y='value', color='variable', barmode='group', color_discrete_map={'UV': COLOR_GREY, 'PV': COLOR_NAVY}, text='value')
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig.update_xaxes(type='category')
            fig.update_layout(legend_title_text=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True, key="summary_daily_chart")
    with c2:
        st.markdown('<div class="sub-header">📈 최근 3달 간 추이 분석</div>', unsafe_allow_html=True)
        if not df_weekly.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df_weekly['주차'], y=df_weekly['UV'], name='UV', marker_color=COLOR_GREY))
            fig2.add_trace(go.Bar(x=df_weekly['주차'], y=df_weekly['PV'], name='PV', marker_color=COLOR_NAVY))
            
            week_labels = df_weekly['주차'].tolist()
            year_boundary_idx = None
            for i, label in enumerate(week_labels):
                week_num = int(re.search(r'\d+', str(label)).group()) if re.search(r'\d+', str(label)) else 0
                if week_num == 1 and i > 0:
                    prev_week_num = int(re.search(r'\d+', str(week_labels[i-1])).group()) if re.search(r'\d+', str(week_labels[i-1])) else 0
                    if prev_week_num == 52:
                        year_boundary_idx = i - 0.5
                        break
            
            if year_boundary_idx is not None:
                fig2.add_vline(x=year_boundary_idx, line_dash="dot", line_width=1, line_color="#78909c", opacity=0.7, annotation_text="2025/2026", annotation_position="top", annotation_font_size=10, annotation_font_color="#78909c")
            
            fig2.update_layout(barmode='group', plot_bgcolor='white', margin=dict(t=30), yaxis=dict(tickformat=","), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig2, use_container_width=True, key="summary_weekly_chart")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 활성 기사 수: 클릭이 발생한 기사 경로 수 (GA4 pagePath 기준)<br>
    • 발행 기사 수: 해당 주차에 신규 발행된 기사 건수 (발행일시 기준)<br>
    • 조회수(PV): GA4 screenPageViews 합계<br>
    • 방문자수(UV): GA4 activeUsers 합계<br>
    • 방문자당 페이지뷰: PV ÷ UV<br>
    • 신규 방문자 비율: (신규 방문자 수 ÷ 전체 방문자 수) × 100<br>
    &nbsp;&nbsp;&nbsp;&nbsp;※ 신규 방문자 수: GA4 newUsers (해당 기간 동안 처음 방문한 사용자 수)<br>
    • 검색 유입 비율: (검색엔진 유입 조회수 ÷ 전체 조회수) × 100
    </div>
    """, unsafe_allow_html=True)

# ----------------- 2. 접근 경로 -----------------
def render_traffic(df_traffic_curr, df_traffic_last):
    st.markdown('<div class="section-header-container"><div class="section-header">2. 주간 접근 경로 분석</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    fig1 = px.pie(df_traffic_curr, names='유입경로', values='조회수', hole=0.5, color_discrete_sequence=CHART_PALETTE)
    fig1.update_layout(height=350, showlegend=True, margin=dict(t=30, b=80, l=40, r=40))
    with c1: st.plotly_chart(fig1, use_container_width=True, key="traffic_curr_chart")
    
    fig2 = px.pie(df_traffic_last, names='유입경로', values='조회수', hole=0.5, color_discrete_sequence=CHART_PALETTE)
    fig2.update_layout(height=280, showlegend=True, margin=dict(t=30, b=80, l=40, r=40))
    with c2: st.plotly_chart(fig2, use_container_width=True, key="traffic_last_chart")
    
    st.markdown('<div class="sub-header">주요 유입경로 비중 변화</div>', unsafe_allow_html=True)
    df_m = pd.merge(df_traffic_curr, df_traffic_last, on='유입경로', suffixes=('_이번', '_지난'))
    df_m['이번주 비중'] = (df_m['조회수_이번'] / df_m['조회수_이번'].sum() * 100).round(1)
    df_m['지난주 비중'] = (df_m['조회수_지난'] / df_m['조회수_지난'].sum() * 100).round(1)
    df_m['비중 변화'] = (df_m['이번주 비중'] - df_m['지난주 비중']).round(1)
    
    df_m.sort_values('이번주 비중', ascending=False, inplace=True)
    
    st.dataframe(df_m[['유입경로', '이번주 비중', '지난주 비중', '비중 변화']].copy().assign(**{'비중 변화': lambda x: x['비중 변화'].apply(lambda v: f"{v:+.1f}%p")}), use_container_width=True, hide_index=True, height="content")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 유입경로별 조회수: GA4 sessionSource별 screenPageViews 합계<br>
    • 비중: (해당 유입경로 조회수 ÷ 전체 조회수) × 100<br>
    • 비중 변화: 이번주 비중 - 지난주 비중 (%p)
    </div>
    """, unsafe_allow_html=True)

# ----------------- 3. 방문자 특성 (지역) -----------------
def render_demo_region(df_region_curr, df_region_last):
    st.markdown('<div class="section-header-container"><div class="section-header">3. 주간 전체 방문자 특성 분석 (지역)</div></div>', unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>지역별 분석</div>", unsafe_allow_html=True)
    c_curr, c_last = st.columns(2)
    custom_margin = dict(t=20, b=20, l=0, r=0)
    
    with c_curr:
        st.markdown(f"**이번주**")
        fig_c = create_donut_chart_with_val(df_region_curr, '구분', 'activeUsers', None, height=350, margin=custom_margin, rotation=90, show_legend=True, limit_labels=5)
        fig_c.update_traces(textfont_size=11)
        st.plotly_chart(fig_c, use_container_width=True, key="region_curr_chart")
        
    with c_last:
        st.markdown(f"**지난주 (비교)**")
        fig_l = create_donut_chart_with_val(df_region_last, '구분', 'activeUsers', None, height=280, margin=custom_margin, rotation=90, show_legend=True, limit_labels=5)
        fig_l.update_traces(textfont_size=11)
        st.plotly_chart(fig_l, use_container_width=True, key="region_last_chart")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if not df_region_curr.empty or not df_region_last.empty:
        df_change = pd.merge(df_region_curr, df_region_last, on='구분', suffixes=('_이번', '_지난'), how='outer').fillna(0)
        total_c = df_change['activeUsers_이번'].sum()
        total_l = df_change['activeUsers_지난'].sum()
        df_change['비율_이번'] = (df_change['activeUsers_이번'] / total_c * 100).round(1) if total_c > 0 else 0
        df_change['비율_지난'] = (df_change['activeUsers_지난'] / total_l * 100).round(1) if total_l > 0 else 0
        df_change['변화(%p)'] = df_change['비율_이번'] - df_change['비율_지난']
        
        df_norm = df_change[df_change['구분']!='기타'].sort_values('activeUsers_이번', ascending=False)
        df_oth = df_change[df_change['구분']=='기타']
        df_disp = pd.concat([df_norm, df_oth])
        
        df_disp['이번주(%)'] = df_disp['비율_이번'].astype(str) + '%'
        df_disp['지난주(%)'] = df_disp['비율_지난'].astype(str) + '%'
        df_disp['변화(%p)'] = df_disp['변화(%p)'].apply(lambda x: f"{x:+.1f}%p")
        st.dataframe(df_disp[['구분', '이번주(%)', '지난주(%)', '변화(%p)']], use_container_width=True, hide_index=True, height="content")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 지역별 비율: (해당 지역 방문자 수 ÷ 전체 방문자 수) × 100<br>
    • 변화(%p): 이번주 비율 - 지난주 비율
    </div>
    """, unsafe_allow_html=True)

# ----------------- 3. 방문자 특성 (연령/성별) -----------------
def render_demo_age_gender(df_age_curr, df_age_last, df_gender_curr, df_gender_last):
    st.markdown('<div class="section-header-container"><div class="section-header">3. 주간 전체 방문자 특성 분석 (연령/성별)</div></div>', unsafe_allow_html=True)
    sub_titles = ['연령별', '성별']
    curr_data = [df_age_curr, df_gender_curr]
    last_data = [df_age_last, df_gender_last]
    color_maps = [None, COLOR_GENDER]
    
    for i in range(2):
        st.markdown(f"<div class='sub-header'>{sub_titles[i]} 분석</div>", unsafe_allow_html=True)
        c_curr, c_last = st.columns(2)
        d_c = curr_data[i]
        d_l = last_data[i]
        
        with c_curr:
            st.markdown(f"**이번주**")
            if d_c.empty or d_c['activeUsers'].sum() == 0:
                st.warning("⚠️ 이번주 데이터 없음 (GA4 비식별 처리)")
            else:
                st.plotly_chart(create_donut_chart_with_val(d_c, '구분', 'activeUsers', color_maps[i]), use_container_width=True, key=f"demo_curr_{i}_chart")
        with c_last:
            st.markdown(f"**지난주 (비교)**")
            if d_l.empty or d_l['activeUsers'].sum() == 0:
                st.info("지난주 데이터 없음")
            else:
                st.plotly_chart(create_donut_chart_with_val(d_l, '구분', 'activeUsers', color_maps[i], height=280), use_container_width=True, key=f"demo_last_{i}_chart")

        if not d_c.empty or not d_l.empty:
            df_change = pd.merge(d_c, d_l, on='구분', suffixes=('_이번', '_지난'), how='outer').fillna(0)
            total_c = df_change['activeUsers_이번'].sum()
            total_l = df_change['activeUsers_지난'].sum()
            df_change['비율_이번'] = (df_change['activeUsers_이번'] / total_c * 100).round(1) if total_c > 0 else 0
            df_change['비율_지난'] = (df_change['activeUsers_지난'] / total_l * 100).round(1) if total_l > 0 else 0
            df_change['변화(%p)'] = df_change['비율_이번'] - df_change['비율_지난']
            df_norm = df_change[df_change['구분']!='기타'].sort_values('activeUsers_이번', ascending=False)
            df_oth = df_change[df_change['구분']=='기타']
            df_disp = pd.concat([df_norm, df_oth])
            df_disp['이번주(%)'] = df_disp['비율_이번'].astype(str) + '%'
            df_disp['지난주(%)'] = df_disp['비율_지난'].astype(str) + '%'
            df_disp['변화(%p)'] = df_disp['변화(%p)'].apply(lambda x: f"{x:+.1f}%p")
            st.dataframe(df_disp[['구분', '이번주(%)', '지난주(%)', '변화(%p)']], use_container_width=True, hide_index=True, height="content")
        st.markdown("<hr>", unsafe_allow_html=True)
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 연령별 비율: (해당 연령 방문자 수 ÷ 전체 방문자 수) × 100<br>
    • 성별 비율: (해당 성별 방문자 수 ÷ 전체 방문자 수) × 100<br>
    • 변화(%p): 이번주 비율 - 지난주 비율
    </div>
    """, unsafe_allow_html=True)

# ----------------- 4. Top 10 상세 -----------------
def render_top10_detail(df_top10):
    st.markdown('<div class="section-header-container"><div class="section-header">4. 최근 7일 조회수 TOP 10 기사 상세</div></div>', unsafe_allow_html=True)
    if not df_top10.empty:
        from utils import clean_author_name
        df_p4 = df_top10.copy()
        def safe_format_int(x):
            try: return f"{int(float(x)):,}"
            except: return str(x)
        for c in ['전체조회수','전체방문자수','좋아요','댓글']: 
            df_p4[c] = df_p4[c].apply(safe_format_int)
        # 작성자에서 직함 제거 (1어절만 남김)
        if '작성자' in df_p4.columns:
            df_p4['작성자'] = df_p4['작성자'].apply(clean_author_name)
        df_p4_display = df_p4.copy()
        df_p4_display = df_p4_display.rename(columns={
            '전체조회수': '최근 7일간 조회수',
            '전체방문자수': '최근 7일간 방문자수',
            '체류시간_fmt': '체류시간',
            '최다유입': '최다 유입경로'
        })
        cols = ['순위','카테고리','세부카테고리','제목','작성자','발행일시','최근 7일간 조회수','최근 7일간 방문자수','신규방문자비율','최다 유입경로','체류시간','좋아요','댓글']
        st.dataframe(df_p4_display[cols], use_container_width=True, hide_index=True, height="content")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 조회수: GA4 screenPageViews (최근 7일간)<br>
    • 방문자수: GA4 activeUsers (최근 7일간)<br>
    • 신규방문자비율: (신규 방문자 수 ÷ 전체 방문자 수) × 100<br>
    • 체류시간: GA4 userEngagementDuration 평균<br>
    • 순위: 조회수 기준 내림차순 정렬
    </div>
    """, unsafe_allow_html=True)

# ----------------- 5. Top 10 추이 -----------------
def render_top10_trends(df_top10, df_top10_sources=None):
    st.markdown('<div class="section-header-container"><div class="section-header">5. TOP 10 기사 유입경로(매체)별 조회수 분포</div></div>', unsafe_allow_html=True)
    
    if not df_top10.empty:
        from utils import clean_author_name
        df_p5 = df_top10.copy()
        def safe_format_int_col(x):
            try:
                val_str = str(x).replace(',', '')
                return f"{int(float(val_str)):,}"
            except: return str(x)
        
        # 작성자에서 직함 제거 (1어절만 남김)
        if '작성자' in df_p5.columns:
            df_p5['작성자'] = df_p5['작성자'].apply(clean_author_name)
        
        df_p5['전체조회수_fmt'] = df_p5['전체조회수'].apply(safe_format_int_col)
        df_p5 = df_p5.rename(columns={'전체조회수_fmt': '지난 7일간 조회수'})
        
        cols = ['순위', '제목', '작성자', '발행일시', '지난 7일간 조회수', '유입경로 1순위']
        if '유입경로 1순위' not in df_p5.columns:
            df_p5['유입경로 1순위'] = "-"
            
        st.dataframe(df_p5[cols], use_container_width=True, hide_index=True, height="content")
        
        if df_top10_sources is not None and not df_top10_sources.empty:
            path_to_title = dict(zip(df_top10['경로'], df_top10['제목']))
            df_src = df_top10_sources.copy()
            df_src['기사제목'] = df_src['pagePath'].map(path_to_title).fillna('기타')
            
            df_src['기사제목_short'] = df_src['기사제목'].apply(lambda x: x[:10] + '...' if len(str(x)) > 10 else str(x))
            
            short_titles_ordered = [t[:10] + '...' if len(str(t)) > 10 else str(t) for t in df_top10['제목'].tolist()]
            short_titles_ordered.reverse()
            
            fig = px.bar(
                df_src, 
                x='screenPageViews',   
                y='기사제목_short',     
                color='유입경로',
                text='screenPageViews',
                title='기사별 유입경로 비중',
                orientation='h',       
                color_discrete_sequence=CHART_PALETTE,
                hover_data={'top_detail': True, 'screenPageViews': True, '기사제목': True, '기사제목_short': False}
            )
            
            fig.update_traces(hovertemplate='<b>%{y}</b><br>유입경로: %{legendgroup}<br>상세경로: %{customdata[0]}<br>조회수: %{x}<extra></extra>')
            
            fig.update_layout(
                plot_bgcolor='white',
                xaxis_title='조회수',
                yaxis_title='기사 (요약)',
                legend_title_text='유입경로'
            )
            fig.update_yaxes(categoryorder='array', categoryarray=short_titles_ordered)
            
            st.plotly_chart(fig, use_container_width=True, key="top10_source_distribution_chart")
        else:
            st.warning("기사별 유입경로 상세 데이터가 없습니다.")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 유입경로별 조회수: GA4 sessionSource별 screenPageViews 합계<br>
    • 유입경로 1순위: 해당 기사에 가장 많이 유입된 경로<br>
    • 조회수 분포: 기사별 유입경로(매체)별 조회수 비중
    </div>
    """, unsafe_allow_html=True)

# ----------------- 6. 카테고리 -----------------
def render_category(df_top10, selected_week=None):
    st.markdown('<div class="section-header-container"><div class="section-header">6. 카테고리별 분석</div></div>', unsafe_allow_html=True)
    if not df_top10.empty:
        df_real = df_top10
        
        # 전주 데이터 가져오기
        if selected_week and selected_week in WEEK_MAP:
            dr = WEEK_MAP[selected_week]
            s_dt = dr.split(' ~ ')[0].replace('.', '-')
            e_dt = dr.split(' ~ ')[1].replace('.', '-')
            ls_dt = (datetime.strptime(s_dt, '%Y-%m-%d')-timedelta(days=7)).strftime('%Y-%m-%d')
            le_dt = (datetime.strptime(e_dt, '%Y-%m-%d')-timedelta(days=7)).strftime('%Y-%m-%d')
            
            # 전주 발행 기사 목록 페이지 크롤링
            from data import crawl_article_list_page, crawl_single_article_cached
            import concurrent.futures
            
            published_articles_last_week = []
            for page_num in range(1, 6):  # 최대 5페이지만 확인 (성능 고려)
                articles = crawl_article_list_page(page_num)
                if not articles:
                    break
                for article in articles:
                    pub_date_str = article.get('published_date', '-')
                    if pub_date_str == '-':
                        continue
                    try:
                        date_part = pub_date_str.split()[0] if ' ' in pub_date_str else pub_date_str
                        if '.' in date_part:
                            date_part = date_part.replace('.', '-')
                        pub_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                        ls_dt_date = datetime.strptime(ls_dt, '%Y-%m-%d').date()
                        le_dt_date = datetime.strptime(le_dt, '%Y-%m-%d').date()
                        if ls_dt_date <= pub_date <= le_dt_date:
                            published_articles_last_week.append(article)
                        elif pub_date < ls_dt_date:
                            break  # 더 오래된 기사는 중단
                    except:
                        continue
            
            # 전주 발행 기사의 카테고리 정보 크롤링
            cat_main_last_dict = {}
            cat_sub_last_dict = {}
            scraped_last_week = {}
            if published_articles_last_week:
                last_week_paths = [a['path'] for a in published_articles_last_week[:50]]  # 최대 50개만 (성능 고려)
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(crawl_single_article_cached, path): path for path in last_week_paths}
                    for future in concurrent.futures.as_completed(futures):
                        path = futures[future]
                        try:
                            result = future.result(timeout=3.0)
                            scraped_last_week[path] = result
                        except:
                            scraped_last_week[path] = ("관리자", 0, 0, "뉴스", "이슈", "-")
                
                # 카테고리별 기사 수 집계
                for path, result in scraped_last_week.items():
                    cat = result[3] if len(result) > 3 else "뉴스"
                    subcat = result[4] if len(result) > 4 else "이슈"
                    cat_main_last_dict[cat] = cat_main_last_dict.get(cat, 0) + 1
                    key = (cat, subcat)
                    cat_sub_last_dict[key] = cat_sub_last_dict.get(key, 0) + 1
        else:
            cat_main_last_dict = {}
            cat_sub_last_dict = {}
        
        # 메인 카테고리
        cat_main = df_real.groupby('카테고리').agg(기사수=('제목','count'), 전체조회수=('전체조회수','sum')).reset_index()
        total_main = cat_main['기사수'].sum()
        cat_main['기사수_num'] = cat_main['기사수']
        
        # 전주 카테고리 데이터프레임 생성
        cat_main_last = pd.DataFrame(columns=['카테고리', '기사수'])
        for cat in cat_main['카테고리'].unique():
            count = cat_main_last_dict.get(cat, 0)
            cat_main_last = pd.concat([cat_main_last, pd.DataFrame({'카테고리': [cat], '기사수': [count]})], ignore_index=True)
        
        # 이번주/전주 비교 데이터 준비
        cat_main_compare = cat_main[['카테고리', '기사수_num']].copy()
        cat_main_compare = cat_main_compare.rename(columns={'기사수_num': '이번주'})
        cat_main_compare = pd.merge(cat_main_compare, cat_main_last[['카테고리', '기사수']], on='카테고리', how='left', suffixes=('', '_last'))
        cat_main_compare['전주'] = cat_main_compare['기사수'].fillna(0).astype(int)
        cat_main_compare = cat_main_compare.drop(columns=['기사수'])
        
        # 막대그래프용 데이터 변환
        cat_main_melted = cat_main_compare.melt(id_vars='카테고리', value_vars=['이번주', '전주'], var_name='구분', value_name='기사수')
        
        # 기사수 (비중%) 형태로 병합
        cat_main['기사수'] = cat_main.apply(lambda x: f"{x['기사수']} ({x['기사수']/total_main*100:.1f}%)", axis=1)
        cat_main['전체조회수'] = pd.to_numeric(cat_main['전체조회수'], errors='coerce').fillna(0)
        
        # [수정] 컬럼명 변경: 기사1건당평균 -> 평균조회수
        cat_main['평균조회수'] = (cat_main['전체조회수'] / cat_main['기사수_num']).astype(int).map('{:,}'.format)
        cat_main['전체조회수'] = cat_main['전체조회수'].map('{:,}'.format)
        
        st.markdown('<div class="chart-header">메인 카테고리별 기사 수</div>', unsafe_allow_html=True)
        # 이번주/전주 비교 막대그래프
        max_value = max(cat_main_compare['이번주'].max(), cat_main_compare['전주'].max()) if not cat_main_compare.empty else 0
        fig_main = px.bar(cat_main_melted, x='카테고리', y='기사수', color='구분', barmode='group', 
                          color_discrete_map={'이번주': COLOR_NAVY, '전주': COLOR_GREY},
                          text='기사수')
        fig_main.update_traces(texttemplate='%{text}', textposition='outside')
        fig_main.update_layout(showlegend=True, plot_bgcolor='white', yaxis_title="기사수", 
                              yaxis=dict(range=[0, max_value * 1.2] if max_value > 0 else [0, 10]),
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_main, use_container_width=True, key="category_main_chart")
        st.dataframe(cat_main[['카테고리', '기사수', '전체조회수', '평균조회수']], use_container_width=True, hide_index=True, height="content")

        # 세부 카테고리
        st.markdown('<div class="chart-header">세부 카테고리별 기사 수</div>', unsafe_allow_html=True)
        cat_sub = df_real.groupby(['카테고리', '세부카테고리']).agg(기사수=('제목','count'), 전체조회수=('전체조회수','sum')).reset_index()
        total_sub = cat_sub['기사수'].sum()
        cat_sub['기사수_num'] = cat_sub['기사수']
        
        # 전주 세부 카테고리 데이터
        cat_sub_last = pd.DataFrame(columns=['카테고리', '세부카테고리', '기사수'])
        for (cat, subcat), count in cat_sub_last_dict.items():
            cat_sub_last = pd.concat([cat_sub_last, pd.DataFrame({
                '카테고리': [cat], 
                '세부카테고리': [subcat], 
                '기사수': [count]
            })], ignore_index=True)
        
        # 이번주 카테고리에 없는 전주 카테고리도 추가 (0으로)
        for _, row in cat_sub.iterrows():
            key = (row['카테고리'], row['세부카테고리'])
            if key not in cat_sub_last_dict:
                cat_sub_last = pd.concat([cat_sub_last, pd.DataFrame({
                    '카테고리': [row['카테고리']], 
                    '세부카테고리': [row['세부카테고리']], 
                    '기사수': [0]
                })], ignore_index=True)
        
        # 이번주/전주 비교 데이터 준비
        cat_sub_compare = cat_sub[['카테고리', '세부카테고리', '기사수_num']].copy()
        cat_sub_compare = cat_sub_compare.rename(columns={'기사수_num': '이번주'})
        cat_sub_compare = pd.merge(cat_sub_compare, cat_sub_last[['카테고리', '세부카테고리', '기사수']], 
                                   on=['카테고리', '세부카테고리'], how='left', suffixes=('', '_last'))
        cat_sub_compare['전주'] = cat_sub_compare['기사수'].fillna(0).astype(int)
        cat_sub_compare = cat_sub_compare.drop(columns=['기사수'])
        
        # 막대그래프용 데이터 변환
        cat_sub_melted = cat_sub_compare.melt(id_vars=['카테고리', '세부카테고리'], value_vars=['이번주', '전주'], 
                                              var_name='구분', value_name='기사수')
        
        # [수정] 기사수 (비중%) 형태로 병합
        cat_sub['기사수'] = cat_sub.apply(lambda x: f"{x['기사수']} ({x['기사수']/total_sub*100:.1f}%)", axis=1)
        cat_sub['전체조회수'] = pd.to_numeric(cat_sub['전체조회수'], errors='coerce').fillna(0)
        
        # [수정] 컬럼명 변경: 기사1건당평균 -> 평균조회수
        cat_sub['평균조회수'] = (cat_sub['전체조회수'] / cat_sub['기사수_num']).astype(int).map('{:,}'.format)
        cat_sub['전체조회수'] = cat_sub['전체조회수'].map('{:,}'.format)
        
        # 이번주/전주 비교 막대그래프
        max_value_sub = max(cat_sub_compare['이번주'].max(), cat_sub_compare['전주'].max()) if not cat_sub_compare.empty else 0
        fig_sub = px.bar(cat_sub_melted, x='세부카테고리', y='기사수', color='구분', barmode='group',
                        color_discrete_map={'이번주': COLOR_NAVY, '전주': COLOR_GREY},
                        text='기사수')
        fig_sub.update_traces(texttemplate='%{text}', textposition='outside')
        fig_sub.update_layout(plot_bgcolor='white', yaxis_title="기사수",
                             yaxis=dict(range=[0, max_value_sub * 1.2] if max_value_sub > 0 else [0, 10]),
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sub, use_container_width=True, key="category_sub_chart")
        st.dataframe(cat_sub[['카테고리', '세부카테고리', '기사수', '전체조회수', '평균조회수']], use_container_width=True, hide_index=True, height="content")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 기사 수: 카테고리별 기사 수 (비중% 포함)<br>
    • 전체조회수: 카테고리별 기사 조회수 합계<br>
    • 평균조회수: 카테고리 전체 조회수 ÷ 카테고리 기사 수<br>
    • 비중: (카테고리 기사 수 ÷ 전체 기사 수) × 100
    </div>
    """, unsafe_allow_html=True)

# ----------------- 7. 기자 (통합) -----------------
def render_writer_integrated(writers_df, df_all_articles_with_metadata):
    st.markdown('<div class="section-header-container"><div class="section-header">7. 이번주 기자별 분석</div></div>', unsafe_allow_html=True)
    
    if not df_all_articles_with_metadata.empty and '작성자' in df_all_articles_with_metadata.columns:
        # 본명 기준: 본명별 합산
        from data import AUTHOR_MAPPING_DATA
        from utils import clean_author_name
        pen_to_real_map = {item['필명']: item['본명'] for item in AUTHOR_MAPPING_DATA}
        
        df_work = df_all_articles_with_metadata.copy()
        # 작성자 이름에서 직함 제거 (한 번 더 정리)
        df_work['작성자'] = df_work['작성자'].apply(clean_author_name)
        df_work['본명'] = df_work['작성자'].map(pen_to_real_map).fillna(df_work['작성자'])
        
        # 본명 기준 집계
        writers_by_real = df_work.groupby('본명').agg(
            기사수=('제목','count'), 
            총조회수=('전체조회수','sum'),
            좋아요=('좋아요', 'sum'),
            댓글=('댓글', 'sum')
        ).reset_index()
        writers_by_real = writers_by_real.sort_values('총조회수', ascending=False)
        writers_by_real['순위'] = range(1, len(writers_by_real)+1)
        writers_by_real['평균조회수'] = (writers_by_real['총조회수']/writers_by_real['기사수']).astype(int)
        
        # 비율 계산 (각 지표 중에서의 점유율)
        total_views = writers_by_real['총조회수'].sum()
        total_avg_views = writers_by_real['평균조회수'].sum()  # 평균 조회수 합계 (점유율 계산용)
        
        st.markdown('<div class="sub-header">본명 기준(전체 조회수 기준)</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.75rem; color: #78909c; margin-bottom: 5px;">(건, %)</div>', unsafe_allow_html=True)
        
        disp_w = writers_by_real.copy()
        # 비율 계산 및 포맷팅 (각 지표 중에서의 점유율)
        disp_w['총조회수_비율'] = (disp_w['총조회수'] / total_views * 100).round(1) if total_views > 0 else 0
        disp_w['평균조회수_비율'] = (disp_w['평균조회수'] / total_avg_views * 100).round(1) if total_avg_views > 0 else 0
        
        # 포맷팅: 숫자 + 비율
        disp_w['총조회수_포맷'] = disp_w.apply(lambda x: f"{x['총조회수']:,} ({x['총조회수_비율']:.1f}%)", axis=1)
        disp_w['평균조회수_포맷'] = disp_w.apply(lambda x: f"{x['평균조회수']:,} ({x['평균조회수_비율']:.1f}%)", axis=1)
        disp_w['좋아요_포맷'] = disp_w['좋아요'].apply(lambda x: f"{x:,}")
        disp_w['댓글_포맷'] = disp_w['댓글'].apply(lambda x: f"{x:,}")
        
        # 본명에서 직함 제거 (1어절만 남김)
        disp_w['본명'] = disp_w['본명'].apply(clean_author_name)
        
        disp_w = disp_w[['순위', '본명', '기사수', '총조회수_포맷', '평균조회수_포맷', '좋아요_포맷', '댓글_포맷']]
        disp_w.columns = ['순위', '본명', '발행기사 수', '전체 조회수', '기사 1건당 조회수', '좋아요 개수', '댓글 개수']
        
        st.dataframe(
            disp_w, 
            use_container_width=True, 
            hide_index=True,
            height="content",
            column_config={
                "순위": st.column_config.NumberColumn("순위", format="%d"),
                "본명": st.column_config.TextColumn("본명"),
                "발행기사 수": st.column_config.NumberColumn("발행기사 수", format="%d"),
                "전체 조회수": st.column_config.TextColumn("전체 조회수"),
                "기사 1건당 조회수": st.column_config.TextColumn("기사 1건당 조회수"),
                "좋아요 개수": st.column_config.TextColumn("좋아요 개수"),
                "댓글 개수": st.column_config.TextColumn("댓글 개수")
            }
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 필명 기준: 필명별 합산 (모든 필명 포함)
        df_work_pen = df_all_articles_with_metadata.copy()
        # 작성자 이름에서 직함 제거 (한 번 더 정리)
        df_work_pen['작성자'] = df_work_pen['작성자'].apply(clean_author_name)
        df_work_pen['본명_mapped'] = df_work_pen['작성자'].map(pen_to_real_map)
        # 필명 기준은 모든 작성자(필명)를 포함 (본명과 같은 경우도 포함)
        # 단, 매핑이 없는 경우는 본명으로 사용
        df_work_pen['본명'] = df_work_pen['본명_mapped'].fillna(df_work_pen['작성자'])
        
        if not df_work_pen.empty:
            writers_by_pen = df_work_pen.groupby('작성자').agg(
                기사수=('제목','count'), 
                총조회수=('전체조회수','sum'),
                좋아요=('좋아요', 'sum'),
                댓글=('댓글', 'sum')
            ).reset_index()
            writers_by_pen = writers_by_pen.rename(columns={'작성자': '필명'})
            # 본명 매핑 (매핑이 없으면 필명 그대로)
            writers_by_pen['본명'] = writers_by_pen['필명'].map(pen_to_real_map).fillna(writers_by_pen['필명'])
            writers_by_pen = writers_by_pen.sort_values('총조회수', ascending=False)
            writers_by_pen['순위'] = range(1, len(writers_by_pen)+1)
            writers_by_pen['평균조회수'] = (writers_by_pen['총조회수']/writers_by_pen['기사수']).astype(int)
            
            # 비율 계산 (각 지표 중에서의 점유율)
            total_views_pen = writers_by_pen['총조회수'].sum()
            total_avg_views_pen = writers_by_pen['평균조회수'].sum()  # 평균 조회수 합계 (점유율 계산용)
            
            st.markdown('<div class="sub-header">필명 기준(전체 조회수 기준)</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.75rem; color: #78909c; margin-bottom: 5px;">(건, %)</div>', unsafe_allow_html=True)
            
            disp_w_pen = writers_by_pen.copy()
            # 비율 계산 및 포맷팅 (각 지표 중에서의 점유율)
            disp_w_pen['총조회수_비율'] = (disp_w_pen['총조회수'] / total_views_pen * 100).round(1) if total_views_pen > 0 else 0
            disp_w_pen['평균조회수_비율'] = (disp_w_pen['평균조회수'] / total_avg_views_pen * 100).round(1) if total_avg_views_pen > 0 else 0
            
            # 포맷팅: 숫자 + 비율
            disp_w_pen['총조회수_포맷'] = disp_w_pen.apply(lambda x: f"{x['총조회수']:,} ({x['총조회수_비율']:.1f}%)", axis=1)
            disp_w_pen['평균조회수_포맷'] = disp_w_pen.apply(lambda x: f"{x['평균조회수']:,} ({x['평균조회수_비율']:.1f}%)", axis=1)
            disp_w_pen['좋아요_포맷'] = disp_w_pen['좋아요'].apply(lambda x: f"{x:,}")
            disp_w_pen['댓글_포맷'] = disp_w_pen['댓글'].apply(lambda x: f"{x:,}")
            
            # 본명, 필명에서 직함 제거 (1어절만 남김)
            disp_w_pen['본명'] = disp_w_pen['본명'].apply(clean_author_name)
            disp_w_pen['필명'] = disp_w_pen['필명'].apply(clean_author_name)
            
            disp_w_pen = disp_w_pen[['순위', '필명', '본명', '기사수', '총조회수_포맷', '평균조회수_포맷', '좋아요_포맷', '댓글_포맷']]
            disp_w_pen.columns = ['순위', '필명', '본명', '발행기사 수', '전체 조회수', '기사 1건당 조회수', '좋아요 개수', '댓글 개수']
            
            st.dataframe(
                disp_w_pen, 
                use_container_width=True, 
                hide_index=True,
                height="content",
                column_config={
                    "순위": st.column_config.NumberColumn("순위", format="%d"),
                    "필명": st.column_config.TextColumn("필명"),
                    "본명": st.column_config.TextColumn("본명"),
                    "발행기사 수": st.column_config.NumberColumn("발행기사 수", format="%d"),
                    "전체 조회수": st.column_config.TextColumn("전체 조회수"),
                    "기사 1건당 조회수": st.column_config.TextColumn("기사 1건당 조회수"),
                    "좋아요 개수": st.column_config.TextColumn("좋아요 개수"),
                    "댓글 개수": st.column_config.TextColumn("댓글 개수")
                }
            )
        else: 
            st.info("필명 기자 실적 없음")
    
    # 산식 각주
    st.markdown("""
    <div style='font-size: 0.85rem; color: #78909c; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0;'>
    <strong>산식:</strong><br>
    • 발행기사 수: 기자별 기사 수 합계<br>
    • 전체 조회수: 기자별 기사 조회수 합계 (전체 대비 비율 %)<br>
    • 기사 1건당 조회수: 총조회수 ÷ 발행기사 수 (전체 대비 비율 %)<br>
    • 순위: 총조회수 기준 내림차순 정렬
    </div>
    """, unsafe_allow_html=True)

# ----------------- 7. 기자 (본명) - 하위 호환성 유지 -----------------
def render_writer_real(writers_df):
    st.markdown('<div class="section-header-container"><div class="section-header">7. 이번주 기자별 분석 (본명 기준)</div></div>', unsafe_allow_html=True)
    if not writers_df.empty:
        disp_w = writers_df.copy()
        for c in ['총조회수','평균조회수','좋아요','댓글']: disp_w[c] = disp_w[c].apply(lambda x: f"{x:,}")
        disp_w = disp_w[['순위', '작성자', '필명', '기사수', '총조회수', '평균조회수', '좋아요', '댓글']]
        disp_w.columns = ['순위', '본명', '필명', '발행기사 수', '전체 조회 수', '기사 1건 당 평균 조회 수', '좋아요 개수', '댓글 개수']
        st.dataframe(disp_w, use_container_width=True, hide_index=True, height="content")

# ----------------- 8. 기자 (필명) - 하위 호환성 유지 -----------------
def render_writer_pen(writers_df):
    st.markdown('<div class="section-header-container"><div class="section-header">8. 이번주 기자별 분석 (필명 기준)</div></div>', unsafe_allow_html=True)
    if not writers_df.empty:
        df_pen = writers_df[writers_df['필명'] != ''].copy()
        if not df_pen.empty:
            df_pen['순위'] = df_pen['총조회수'].rank(method='min', ascending=False).astype(int)
            df_pen = df_pen.sort_values('순위')
            disp_w = df_pen.copy()
            for c in ['총조회수','평균조회수','좋아요','댓글']: disp_w[c] = disp_w[c].apply(lambda x: f"{x:,}")
            disp_w = disp_w[['순위', '필명', '작성자', '기사수', '총조회수', '평균조회수', '좋아요', '댓글']]
            disp_w.columns = ['순위', '필명', '본명', '발행기사 수', '전체 조회 수', '기사 1건 당 평균 조회 수', '좋아요 개수', '댓글 개수']
            st.dataframe(disp_w, use_container_width=True, hide_index=True, height="content")
        else: st.info("필명 기자 실적 없음")