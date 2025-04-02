import pandas as pd
from missing_data_handler import MissingDataHandler  


class Preprocessor1:
    def __init__(self, file_paths: dict):
        """
        file_paths: { "brazil_varginha": "경로.csv", ... }
        """
        self.file_paths = file_paths
        self.data = {}

    def load_data(self):
        for name, path in self.file_paths.items():
            df = pd.read_csv(path)
            df.replace(-999, pd.NA, inplace=True)
            self.data[name] = df

    def weather_preprocess(self):
        for name, df in self.data.items():
            if 'WSC' in df.columns:
                df.drop(columns=['WSC'], inplace=True)

            df["Date"] = df["YEAR"].astype(str) + "-" + \
                         df["MO"].astype(str).str.zfill(2) + "-" + \
                         df["DY"].astype(str).str.zfill(2)
            df.drop(columns=["YEAR", "MO", "DY"], inplace=True)

            cols = ["Date"] + [col for col in df.columns if col != "Date"]
            df = df[cols]

            missing_cols = df.columns[df.isna().any()].tolist()
            if 'Date' in missing_cols:
                missing_cols.remove('Date')

            handler = MissingDataHandler(df, date_col="Date")
            df_filled = handler.fill_by_monthly_avg(cols=missing_cols)

            self.data[name] = df_filled

    def propagate_missing_values(self, df: pd.DataFrame, max_days: int = 7):
        for shift_day in range(1, max_days + 1):
            df.fillna(df.shift(shift_day), inplace=True)
        df.fillna(method='bfill', inplace=True)
        return df

    def add_return_column(self, df: pd.DataFrame, price_col='Coffee_Price', return_col='Coffee_Return'):
        if price_col in df.columns:
            df[return_col] = df[price_col].pct_change().fillna(0).round(4)
        return df

    def save(self, save_dir: str):
        for name, df in self.data.items():
            save_path = f"{save_dir}/{name}.csv"
            df.to_csv(save_path, index=False)
            print(f"✅ 저장 완료: {save_path}")

    def run_all(self, save_dir="../data/processed1"):
        # 1. 날씨 데이터 전처리
        weather_paths = {
            "brazil_varginha": "../data/raw/브라질-Varginha.csv",
            "brazil_carmo_de_minas": "../data/raw/브라질-Carmo de Minas.csv",
            "brazil_patrocinio": "../data/raw/브라질-patrocinio.csv",
            "ethiopia_limu": "../data/raw/에티오피아-Limu.csv",
            "ethiopia_sidamo": "../data/raw/에티오피아-Sidamo.csv",
            "ethiopia_yirgacheffe": "../data/raw/에티오피아-Yirgacheffe.csv",
            "colombia_manizales": "../data/raw/콜롬비아-마니살레스.csv",
            "colombia_armenia": "../data/raw/콜롬비아-아르메니아.csv",
            "colombia_pereira": "../data/raw/콜롬비아-페레이라.csv"
        }

        print("🌀 날씨 데이터 전처리 시작")
        self.file_paths = weather_paths
        self.load_data()
        self.weather_preprocess()
        self.save(save_dir)

        # 2. 마켓 데이터 전처리
        market_paths = {
            "market_data": "../data/raw/market_data.csv",
            "coffee_c_price": "../data/raw/coffee_c_price.csv",
        }

        print("💹 마켓 데이터 전처리 시작")
        self.file_paths = market_paths
        self.data = {}
        self.load_data()

        for name, df in self.data.items():
            df = self.propagate_missing_values(df)

            if name == "coffee_c_price":
                df = self.add_return_column(df)

            self.data[name] = df

        self.save(save_dir)
