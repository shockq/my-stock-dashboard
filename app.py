import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="나의 주식 포트폴리오", layout="wide")

st.title("📊 나의 관심 종목 대시보드 (RSI & 거래량 탑재)")

# 1. 사이드바: 종목 관리 세션
st.sidebar.header("📌 포트폴리오 관리")
default_stocks = ['AAPL', 'TSLA', 'NVDA', '005930.KS']
selected_stocks = st.sidebar.multiselect("분석할 종목을 선택하세요", default_stocks, default="AAPL")

st.sidebar.subheader("💰 가상 매수 정보 설정")
buy_prices = {}
for stock in selected_stocks:
    buy_prices[stock] = st.sidebar.number_input(f"{stock} 매수 단가", value=150.0, key=f"buy_{stock}")

# 2. 메인 화면
if not selected_stocks:
    st.info("왼쪽 사이드바에서 종목을 선택해 주세요.")
else:
    for ticker in selected_stocks:
        with st.expander(f"📈 {ticker} 종합 분석", expanded=True):
            data = yf.download(ticker, period="1y", interval="1d")
            
            if not data.empty:
                # 데이터 안전 추출
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
                
                # 상단 지표 표시
                c1, c2, c3 = st.columns(3)
                c1.metric("현재가", f"${curr_price:.2f}" if ".KS" not in ticker else f"{int(curr_price)}원")
                c2.metric("매수가", f"${my_price:.2f}" if ".KS" not in ticker else f"{int(my_price)}원")
                c3.metric("수익률", f"{percent:.2f}%", delta=f"{change:.2f}")

                # ---------------- 지표 계산 ----------------
                # 1) 이동평균선
                ma20 = close_s.rolling(window=20).mean()
                
                # 2) RSI (14일 기준) 계산
                delta = close_s.diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                ema_up = up.ewm(com=13, adjust=False).mean()
                ema_down = down.ewm(com=13, adjust=False).mean()
                rs = ema_up / ema_down
                rsi = 100 - (100 / (1 + rs))
                curr_rsi = float(rsi.iloc[-1])

                # ---------------- AI 상태 판단 메시지 ----------------
                st.markdown("#### 💡 현재 상태 분석")
                msg_col1, msg_col2 = st.columns(2)
                
                with msg_col1:
                    if curr_price > float(ma20.iloc[-1]):
                        st.success("✅ **추세:** 20일 이평선 위 (상승 흐름 유지)")
                    else:
                        st.warning("⚠️ **추세:** 20일 이평선 아래 (하락 주의)")
                        
                with msg_col2:
                    if curr_rsi >= 70:
                        st.error(f"🔥 **RSI ({curr_rsi:.1f}):** 과매수 구간! (사람들이 너무 많이 샀습니다. 단기 고점일 수 있으니 신규 매수는 피하세요.)")
                    elif curr_rsi <= 30:
                        st.info(f"❄️ **RSI ({curr_rsi:.1f}):** 과매도 구간! (너무 많이 떨어졌습니다. 반등을 노린 매수 기회일 수 있습니다.)")
                    else:
                        st.success(f"⚖️ **RSI ({curr_rsi:.1f}):** 중립 구간 (안정적인 상태입니다.)")

                # ---------------- 3단 복합 차트 그리기 ----------------
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.05, row_heights=[0.5, 0.25, 0.25])

                # [Row 1] 캔들 차트 + 이평선
                fig.add_trace(go.Candlestick(x=data.index, open=open_s, high=high_s, low=low_s, close=close_s, name='주가'), row=1, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=ma20, name='20일 이평선', line=dict(color='orange')), row=1, col=1)

                # [Row 2] 거래량 차트 (상승 시 빨강, 하락 시 파랑)
                vol_colors = ['#ff5050' if close_s.iloc[i] > open_s.iloc[i] else '#5050ff' for i in range(len(close_s))]
                fig.add_trace(go.Bar(x=data.index, y=vol_s, marker_color=vol_colors, name='거래량'), row=2, col=1)

                # [Row 3] RSI 지표
                fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')), row=3, col=1)
                # RSI 30, 70 기준선 점선 표시
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

                # 차트 디자인 정리
                fig.update_layout(height=700, margin=dict(l=0, r=0, b=0, t=30), showlegend=False)
                fig.update_yaxes(title_text="주가", row=1, col=1)
                fig.update_yaxes(title_text="거래량", row=2, col=1)
                fig.update_yaxes(title_text="RSI 지수", range=[0, 100], row=3, col=1)
                fig.update_xaxes(rangeslider_visible=False) # 깔끔함을 위해 기본 범위 슬라이더 숨김

                st.plotly_chart(fig, use_container_width=True)
