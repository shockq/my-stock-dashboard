import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="나의 주식 투자 대시보드", layout="wide")

st.title("📈 초보 투자자를 위한 스마트 대시보드")
st.sidebar.header("설정")

# 1. 종목 관리 (가상 매수 기능 포함)
# 실제로는 DB나 파일에 저장해야 하지만, 일단 리스트 형태로 구현
watched_stocks = st.sidebar.text_input("관심 종목 입력 (예: AAPL, TSLA, 005930.KS)", "AAPL")
my_buy_price = st.sidebar.number_input("나의 매수 단가 (가상)", value=150.0)

# 데이터 가져오기
data = yf.download(watched_stocks, period="1y", interval="1d")

# 기존 20~27번 줄 근처를 아래 내용으로 교체하세요
if not data.empty:
    # 데이터를 확실하게 숫자형(float)으로 변환하여 마지막 값 추출
    curr_price = float(data['Close'].iloc[-1])
    
    # 2. 상단 지표 (손익 현황)
    col1, col2, col3 = st.columns(3)
    
    # 현재가 표시
    col1.metric("현재가", f"${curr_price:.2f}")
    
    # 매수 단가와 수익률 계산
    change = curr_price - my_buy_price
    percent = (change / my_buy_price) * 100
    
    col2.metric("나의 매수가", f"${my_buy_price:.2f}")
    col3.metric("현재 손익", f"{change:.2f} ({percent:.2f}%)", delta=f"{percent:.2f}%")

    # 3. 판단 근거 (기술적 지표 계산)
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA60'] = data['Close'].rolling(window=60).mean()
    
    st.subheader("🔍 AI 투자 판단 근거")
    last_ma20 = data['MA20'].iloc[-1]
    if curr_price > last_ma20:
        st.success(f"**판단:** 현재 주가가 20일 이동평균선(${last_ma20:.2f}) 위에 있습니다. **상승 추세**로 볼 수 있습니다.")
    else:
        st.warning(f"**판단:** 현재 주가가 20일 이동평균선(${last_ma20:.2f}) 아래에 있습니다. **주의**가 필요합니다.")

    # 4. 인터랙티브 차트
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='주가'))
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name='20일 이평선', line=dict(color='orange')))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("종목 코드를 확인해 주세요.")
