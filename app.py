import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="나의 주식 포트폴리오", layout="wide")

st.title("📊 나의 관심 종목 대시보드")

# 1. 사이드바: 종목 및 기간 관리
st.sidebar.header("📌 포트폴리오 관리")
default_stocks = ['AAPL', 'TSLA', 'NVDA', '005930.KS']
selected_stocks = st.sidebar.multiselect("분석할 종목을 선택하세요", default_stocks, default="AAPL")

# ===== [신규 추가] 기간 및 봉 설정 딕셔너리 =====
st.sidebar.subheader("📅 차트 기간 설정")
timeframe_options = {
    "1일 (5분봉)": {"period": "1d", "interval": "5m"},
    "1주일 (15분봉)": {"period": "5d", "interval": "15m"},
    "1개월 (일봉)": {"period": "1mo", "interval": "1d"},
    "1분기 (일봉)": {"period": "3mo", "interval": "1d"},
    "1년 (일봉)": {"period": "1y", "interval": "1d"},
    "3년 (주봉)": {"period": "3y", "interval": "1wk"},
    "5년 (월봉)": {"period": "5y", "interval": "1mo"}
}
selected_tf = st.sidebar.selectbox("조회 기간을 선택하세요", list(timeframe_options.keys()), index=4) # 기본값: 1년(일봉)
tf_params = timeframe_options[selected_tf]

st.sidebar.subheader("💰 가상 매수 정보 설정")
buy_prices = {}
for stock in selected_stocks:
    buy_prices[stock] = st.sidebar.number_input(f"{stock} 매수 단가", value=150.0, key=f"buy_{stock}")

# 2. 메인 화면
if not selected_stocks:
    st.info("왼쪽 사이드바에서 종목을 선택해 주세요.")
else:
    for ticker in selected_stocks:
        with st.expander(f"📈 {ticker} 종합 분석 ({selected_tf})", expanded=True):
            # ===== 선택된 기간과 간격으로 데이터 가져오기 =====
            data = yf.download(ticker, period=tf_params["period"], interval=tf_params["interval"])
            
            if not data.empty:
                if isinstance(data['Close'], pd.Series):
                    close_s, open_s = data['Close'], data['Open']
                    high_s, low_s, vol_s = data['High'], data['Low'], data['Volume']
                else:
                    close_s, open_s = data['Close'][ticker], data['Open'][ticker]
                    high_s, low_s, vol_s = data['High'][ticker], data['Low'][ticker], data['Volume'][ticker]
                
                curr_price = float(close_s.iloc[-1])
                my_price = buy_prices[ticker]
                change = curr_price - my_price
                percent = (change / my_price) * 100
                
                c1, c2, c3 = st.columns(3)
                c1.metric("현재가", f"${curr_price:.2f}" if ".KS" not in ticker else f"{int(curr_price)}원")
                c2.metric("매수가", f"${my_price:.2f}" if ".KS" not in ticker else f"{int(my_price)}원")
                c3.metric("수익률", f"{percent:.2f}%", delta=f"{change:.2f}")

                # 지표 계산
                ma20 = close_s.rolling(window=20).mean() # 일봉이면 20일선, 주봉이면 20주선이 됨
                
                delta = close_s.diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                ema_up = up.ewm(com=13, adjust=False).mean()
                ema_down = down.ewm(com=13, adjust=False).mean()
                rs = ema_up / ema_down
                rsi = 100 - (100 / (1 + rs))
                curr_rsi = float(rsi.iloc[-1])

                st.markdown("#### 💡 현재 상태 분석")
                msg_col1, msg_col2 = st.columns(2)
                
                with msg_col1:
                    # '20일선'이라는 고정된 단어 대신, 선택한 차트에 맞는 표현 사용
                    if curr_price > float(ma20.iloc[-1]):
                        st.success("✅ **추세:** 20선 위 (상승 흐름 유지)")
                    else:
                        st.warning("⚠️ **추세:** 20선 아래 (하락 주의)")
                        
                with msg_col2:
                    if curr_rsi >= 70:
                        st.error(f"🔥 **RSI ({curr_rsi:.1f}):** 과매수 구간! (단기 고점 주의)")
                    elif curr_rsi <= 30:
                        st.info(f"❄️ **RSI ({curr_rsi:.1f}):** 과매도 구간! (반등 기회 탐색)")
                    else:
                        st.success(f"⚖️ **RSI ({curr_rsi:.1f}):** 중립 구간")

                # 차트 그리기
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.05, row_heights=[0.5, 0.25, 0.25])

                fig.add_trace(go.Candlestick(x=data.index, open=open_s, high=high_s, low=low_s, close=close_s, name='주가'), row=1, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=ma20, name='20선', line=dict(color='orange')), row=1, col=1)

                vol_colors = ['#ff5050' if close_s.iloc[i] > open_s.iloc[i] else '#5050ff' for i in range(len(close_s))]
                fig.add_trace(go.Bar(x=data.index, y=vol_s, marker_color=vol_colors, name='거래량'), row=2, col=1)

                fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

                fig.update_layout(height=700, margin=dict(l=0, r=0, b=0, t=30), showlegend=False, hovermode="x unified")
                fig.update_yaxes(title_text="주가", row=1, col=1)
                fig.update_yaxes(title_text="거래량", row=2, col=1)
                fig.update_yaxes(title_text="RSI 지수", range=[0, 100], row=3, col=1)
                fig.update_xaxes(rangeslider_visible=False, showspikes=True, spikemode='across', spikesnap='cursor', spikethickness=1, spikedash='dot', spikecolor='#555555')

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"{ticker}의 데이터를 불러오지 못했습니다. (해당 기간에 데이터가 없을 수 있습니다)")
