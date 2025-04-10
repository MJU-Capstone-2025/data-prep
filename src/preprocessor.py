import pandas as pd
import numpy as np

class CoffeeDataPreprocessor:
    def __init__(self, weather_paths, market_paths):
        self.weather_paths = weather_paths
        self.market_paths = market_paths
        self.weather_all = None
        self.df = None
        self.market_dfs = None

    def load_weather_data(self):
        weather_dfs = {}
        for location, path in self.weather_paths.items():
            df = pd.read_csv(path)
            if "WSC" in df.columns:
                df.drop(columns=["WSC"], inplace=True)
            df["locationName"] = location
            weather_dfs[location] = df

        weather_all = pd.concat(weather_dfs.values(), ignore_index=True)
        weather_all["Date"] = weather_all["YEAR"].astype(str) + "-" + \
                                weather_all["MO"].astype(str).str.zfill(2) + "-" + \
                                weather_all["DY"].astype(str).str.zfill(2)
        weather_all.drop(columns=["YEAR", "MO", "DY"], inplace=True)
        cols = ["Date"] + [col for col in weather_all.columns if col != "Date"]
        weather_all = weather_all[cols]

        selected_features = [
            'Date', 'T2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', 'ALLSKY_SFC_UV_INDEX',
            'PRECTOTCORR', 'RH2M', 'PS', 'locationName']
        weather_all = weather_all[selected_features]
        weather_all.replace(-999, np.nan, inplace=True)

        weather_all["month"] = pd.to_datetime(weather_all["Date"]).dt.month
        weather_all["ALLSKY_SFC_UV_INDEX"] = weather_all.groupby(["locationName", "month"])["ALLSKY_SFC_UV_INDEX"]\
            .transform(lambda x: x.fillna(x.mean()))
        weather_all.drop(columns=["month"], inplace=True)
        weather_all.dropna(inplace=True)

        self.weather_all = weather_all.copy()

    def get_season_tag(self, month: int, country: str) -> str:
        if country == 'brazil':
            return 'harvest' if 5 <= month <= 9 else 'pre-harvest' if 3 <= month <= 4 else 'off-season'
        elif country == 'colombia':
            return 'harvest' if month in [10, 11, 12, 1] else 'sub_harvest' if month in [4, 5, 6] else 'pre-harvest' if month in [2, 3, 9] else 'off-season'
        elif country == 'ethiopia':
            return 'harvest' if month in [10, 11, 12, 1, 2] else 'pre-harvest' if month in [8, 9] else 'off-season'
        return 'off-season'

    def calculate_days_until_harvest(self, date: pd.Timestamp, start_month: int) -> int:
        this_year = date.year
        next_harvest = pd.Timestamp(year=this_year, month=start_month, day=1)
        if date >= next_harvest:
            next_harvest = pd.Timestamp(year=this_year + 1, month=start_month, day=1)
        return (next_harvest - date).days

    def add_season_features(self):
        df = self.weather_all
        df['Month'] = pd.to_datetime(df['Date']).dt.month.astype(int)
        df['season_tag'] = df.apply(
            lambda row: self.get_season_tag(row['Month'], row['locationName'].split('_')[0].lower()), axis=1)
        df.drop(columns='Month', inplace=True)
        df['harvest_start_month'] = df['locationName'].apply(
            lambda x: {'brazil': 5, 'colombia': 10, 'ethiopia': 10}.get(x.split('_')[0].lower(), 5))
        df['Date'] = pd.to_datetime(df['Date'])
        df['days_until_harvest'] = df.apply(
            lambda row: self.calculate_days_until_harvest(row['Date'], row['harvest_start_month']), axis=1)
        df.drop(columns='harvest_start_month', inplace=True)
        self.weather_all = df.copy()
        self.weather_raw = df.copy()

    def create_lag_features(self):
        df = self.weather_all
        lag_months = [1, 2, 3, 4, 5, 6]
        features_to_lag = ['T2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', 'ALLSKY_SFC_UV_INDEX', 'PRECTOTCORR', 'RH2M', 'PS']
        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values(by=['locationName', 'Date'], inplace=True)
        for lag in lag_months:
            for feature in features_to_lag:
                df[f"{feature}_lag_{lag}m"] = df.groupby("locationName")[feature].shift(lag * 30)
        df.sort_values(by="Date", inplace=True)
        self.weather_all = df.copy()
        self.weather_with_lag = df.copy()

    def merge_market_data(self):
        market_dfs = {name: pd.read_csv(path) for name, path in self.market_paths.items()}
        market_data = market_dfs["market_data"]
        market_data_columns = [col for col in market_data.columns if "USD_" in col or "Coffee" in col or "Crude" in col]
        market_data[market_data_columns] = market_data[market_data_columns].fillna(method="ffill")
        self.weather_all['Date'] = pd.to_datetime(self.weather_all['Date'])
        market_data['Date'] = pd.to_datetime(market_data['Date'])
        df = pd.merge(self.weather_all, market_data, on="Date", how="left")
        df = df[df['Date'] != "2015-01-01"]
        df[market_data_columns] = df[market_data_columns].fillna(method="ffill")
        for col in ["Coffee_Price", "Crude_Oil_Price", "USD_KRW", "USD_BRL", "USD_COP", "USD_ETB"]:
            df[f"{col}_Return"] = df[f"{col}_Return"].fillna(0)
        self.df = df
        self.market_dfs = market_dfs
        self.market = market_data.copy()

    def merge_urea_dap_data(self):
        df = self.df.copy()
        df['month'] = df['Date'].dt.to_period("M").dt.to_timestamp()
        urea_df = self.market_dfs["urea_dap_price_data"].copy()
        urea_df['month'] = pd.to_datetime(urea_df['month'])
        df = pd.merge(df, urea_df, on='month', how='left')
        df.drop(columns=['month'], inplace=True)
        self.df = df

    def merge_economy_data(self):
        df = self.df.copy()
        economy_df = self.market_dfs["economy_data"]
        economy_df['Area'] = economy_df['Area'].str.lower()
        economy_df['Date'] = economy_df['Year'].astype(int)
        df['locationName'] = df['locationName'].str.lower()
        df['country'] = df['locationName'].apply(lambda x: x.split('_')[0])
        df['Year'] = pd.to_datetime(df['Date']).dt.year
        df = pd.merge(df, economy_df, left_on=['country', 'Year'], right_on=['Area', 'Date'], how='left')
        drop_cols = ['Area', 'Date_y', 'country', 'Year', 'Year_x', 'Year_y', 'index']
        df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)
        df.rename(columns={'Date_x': 'Date'}, inplace=True)

        rows_with_na = df.isna().sum(axis=1) > 0
        print(f"결측치가 하나라도 있는 행의 개수/전체 행의 개수: {rows_with_na.sum()}/{df.shape[0]}\n")
        missing_columns = df.isna().sum()
        missing_columns = missing_columns[missing_columns > 0]
        missing_columns = missing_columns[~missing_columns.index.str.contains('lag')]
        print("결측치가 있는 컬럼(lag feature 제외): 결측치 개수")
        print(missing_columns)

        self.df = df

    def save_final_data(self, base_path):
        self.df.to_csv(f"{base_path}/temp_union_data.csv", index=False)
        self.weather_raw.to_csv(f"{base_path}/weather.csv", index=False)
        self.weather_with_lag.to_csv(f"{base_path}/weather_with_lag.csv", index=False)
        self.market.to_csv(f"{base_path}/market.csv", index=False)
        print(f"\n통합 데이터 크기: {self.df.shape}")
        print(f"통합 데이터 및 세부 데이터 저장 완료 (경로: {base_path})")


if __name__ == "__main__":
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

    market_paths = {
        "market_data": "../data/raw/market_data.csv",
        "economy_data": "../data/raw/economy.csv",
        "urea_dap_price_data": "../data/raw/Urea&Dap_prices.csv"
    }

    preprocessor = CoffeeDataPreprocessor(weather_paths, market_paths)
    preprocessor.load_weather_data()
    preprocessor.add_season_features()
    preprocessor.create_lag_features()
    preprocessor.merge_market_data()
    preprocessor.merge_urea_dap_data()
    preprocessor.merge_economy_data()
    preprocessor.save_final_data("../data/preprocessed")
