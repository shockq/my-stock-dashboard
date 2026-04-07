import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="나의 주식 투자 대시보드", layout="wide")

st.title("📈 초보 투자자를 위한 스마트 대시보드")
st.sidebar.header("설정")

# 1. 종목 관리
# 기본값을 하나만 넣도록 수정 (예: AAPL)
ticker_input = st.sidebar.text_input("종목 코드를 하나만 입력하세요 (예: AAPL, TSLA, 005930.KS)", "AAPL").strip()
my_buy_price = st.sidebar.number_input("나의 매수 단가 (가상)", value=150.0)

# 데이터 가져오기 (1년치)
data = yf.download(ticker_input, period="1y", interval="1d")

if not data.empty:
    try:
        # 데이터 구조가 복잡할 경우를 대비해 안전하게 마지막 종가 추출
        if isinstance(data['Close'], pd.Series):
            curr_price = float(data['Close'].iloc[-1])
        else:
            # Multi-index인 경우 해당 종목 열만 추출
            curr_price = float(data['Close'][ticker_input].iloc[-1])
        
        # 2. 상단 지표 (손익 현황)
        col1, col2, col3 = st.columns(3)
        
        change = curr_price - my_buy_price
        percent = (change / my_buy_price) * 100
        
        col1.metric("현재가", f"${curr_price:.2f}")
        col2.metric("나의 매수가", f"${my_buy_price:.2f}")
        col3.metric("현재 손익", f"{change:.2f} ({percent:.2f}%)", delta=f"{percent:.2f}%")

        # 3. 판단 근거 (기술적 지표 계산)
        # 종목이 섞여있을 수 있어 확실히 시리즈 형태로 변환 후 계산
        close_series = data['Close'] if isinstance(data['Close'], pd.Series) else data['Close'][ticker_input]
        ma20 = close_series.rolling(window=20).mean()
        
        st.subheader("🔍 AI 투자 판단 근거")
        last_ma20 = float(ma20.iloc[-1])
        
        if curr_price > last_ma20:
            st.success(f"**판단:** 현재 주가가 20일 이동평균선(${last_ma20:.2f}) 위에 있습니다. **상승 추세**로 볼 수 있습니다.")
        else:
            st.warning(f"**판단:** 현재 주가가 20일 이동평균선(${last_ma20:.2f}) 아래에 있습니다. **주의**가 필요합니다.")

        # 4. 차트 그리기
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index, 
                                     open=data['Open'] if isinstance(data['Open'], pd.Series) else data['Open'][ticker_input],
                                     high=data['High'] if isinstance(data['High'], pd.Series) else data['High'][ticker_input],
                                     low=data['Low'] if isinstance(data['Low'], pd.Series) else data['Low'][ticker_input],
                                     close=close_series, name='주가'))
        fig.add_trace(go.Scatter(x=data.index, y=ma20, name='20일 이평선', line=dict(color='orange')))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
else:
    st.error("데이터를 불러올 수 없습니다. 종목 코드가 정확한지 확인해 주세요.")
