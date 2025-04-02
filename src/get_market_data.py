from datetime import datetime
import yfinance as yf
import pandas as pd

class MarketDataFetcher:
    def __init__(self, start="2015-01-01", end="2025-04-01"):
        self.start = pd.to_datetime(start)
        self.end = pd.to_datetime(end)
        self.data = pd.DataFrame()

    def fetch_daily_data(self):
        print(f"📆 수집 기간: {self.start.date()} ~ {self.end.date()}")

        tickers = {
            'Coffee_Price': 'KC=F',
            'Crude_Oil_Price': 'CL=F',
            'USD_KRW': 'KRW=X',
            'USD_BRL': 'BRL=X',
            'USD_COP': 'COP=X',
            'USD_VND': 'VND=X'
        }

        combined_data = {}

        for name, symbol in tickers.items():
            print(f"📈 {name} 수집 중... ({symbol})")
            try:
                df = yf.Ticker(symbol).history(start=self.start, end=self.end, interval='1d')
                if 'Close' in df:
                    combined_data[name] = df['Close']
                else:
                    print(f"⚠ {name}의 'Close' 데이터 없음")
            except Exception as e:
                print(f"❌ {name} 수집 오류: {e}")

        df = pd.DataFrame(combined_data)
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df = df.groupby("Date").mean().reset_index()

        self.data = df
        print("✅ 데이터 수집 및 정리 완료")

    def save_to_csv(self, path="../data/raw/market_data.csv"):
        if not self.data.empty:
            self.data.to_csv(path, index=False)
            print(f"📁 전체 CSV 저장 완료: {path}")

            coffee_path = "../data/raw/coffee_c_price.csv"
            self.data[['Date', 'Coffee_Price']].to_csv(coffee_path, index=False)
            print(f"📁 커피 가격만 저장 완료: {coffee_path}")
        else:
            print("❌ 저장할 데이터가 없습니다.")

    def run_all(self):
        """전체 실행 흐름 (fetch + save)"""
        self.fetch_daily_data()
        self.save_to_csv()
