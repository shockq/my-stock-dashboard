import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="나의 주식 포트폴리오", layout="wide")

st.title("📊 나의 관심 종목 대시보드")

# 1. 사이드바: 종목 관리 세션
st.sidebar.header("📌 포트폴리오 관리")

# 내가 관심 있는 종목 리스트 (여기에 원하는 종목 코드를 계속 추가하세요)
default_stocks = ['AAPL', 'TSLA', 'NVDA', '005930.KS', '000660.KS']
selected_stocks = st.sidebar.multiselect("분석할 종목을 선택하세요", default_stocks, default="AAPL")

# 가상 매수 정보 (간단하게 딕셔너리로 관리 - 나중에 DB 연동 가능)
# 예: {'AAPL': 150.0, 'TSLA': 200.0}
st.sidebar.subheader("💰 가상 매수 정보 설정")
buy_prices = {}
for stock in selected_stocks:
    buy_prices[stock] = st.sidebar.number_input(f"{stock} 매수 단가", value=150.0, key=f"buy_{stock}")

# 2. 메인 화면: 선택한 종목별로 루프를 돌며 표시
if not selected_stocks:
    st.info("왼쪽 사이드바에서 종목을 선택해 주세요.")
else:
    for ticker in selected_stocks:
        with st.expander(f"📈 {ticker} 분석 결과 보기", expanded=True):
            data = yf.download(ticker, period="1y", interval="1d")
            
            if not data.empty:
                # 데이터 추출 (안전한 방식)
                if isinstance(data['Close'], pd.Series):
                    curr_price = float(data['Close'].iloc[-1])
                else:
                    curr_price = float(data['Close'][ticker].iloc[-1])
                
                my_price = buy_prices[ticker]
                change = curr_price - my_price
                percent = (change / my_price) * 100
                
                # 지표 표시
                c1, c2, c3 = st.columns(3)
                c1.metric("현재가", f"${curr_price:.2f}" if ".KS" not in ticker else f"{int(curr_price)}원")
                c2.metric("매수가", f"${my_price:.2f}" if ".KS" not in ticker else f"{int(my_price)}원")
                c3.metric("수익률", f"{percent:.2f}%", delta=f"{change:.2f}")

                # 이동평균선 계산 및 판단
                close_series = data['Close'] if isinstance(data['Close'], pd.Series) else data['Close'][ticker]
                ma20 = close_series.rolling(window=20).mean()
                last_ma20 = float(ma20.iloc[-1])

                if curr_price > last_ma20:
                    st.success(f"✅ **{ticker} 판단:** 20일 이평선 상회 중 (긍정)")
                else:
                    st.warning(f"⚠️ **{ticker} 판단:** 20일 이평선 하회 중 (주의)")

                # 차트
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=data.index, 
                                             open=data['Open'] if isinstance(data['Open'], pd.Series) else data['Open'][ticker],
                                             high=data['High'] if isinstance(data['High'], pd.Series) else data['High'][ticker],
                                             low=data['Low'] if isinstance(data['Low'], pd.Series) else data['Low'][ticker],
                                             close=close_series, name='주가'))
                fig.add_trace(go.Scatter(x=data.index, y=ma20, name='20일 이평선', line=dict(color='orange')))
                fig.update_layout(height=400, margin=dict(l=0, r=0, b=0, t=0))
                st.plotly_chart(fig, use_container_width=True)
