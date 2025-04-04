import pandas as pd
import glob
import os

class Preprocessor2:
    def __init__(self, selected_features: list, input_dir: str, output_dir: str):
        self.selected_features = selected_features
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.input_files = [
            f for f in glob.glob(f"{self.input_dir}/*.csv")
            if "coffee" not in f and "market" not in f
        ]
        os.makedirs(self.output_dir, exist_ok=True)

    def run_all(self):
        for file in self.input_files:
            filename = os.path.basename(file)
            country = filename.split("_")[0].lower()
            print(f"\n🔍 처리 중: {filename} | 국가: {country}")

            df = pd.read_csv(file)

            # 1. Feature 축소
            df = self._reduce_features(df)

            # 2. Coffee 관련 결측치 채우기
            df = self._fill_missing_coffee_values(df)

            # 3. 파생 컬럼 추가
            df = self._add_derived_features(df, country)

            # 저장
            save_path = os.path.join(self.output_dir, filename)
            df.to_csv(save_path, index=False)
            print(f"✅ 저장 완료: {save_path}")

    def _fill_missing_coffee_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Coffee_Price는 앞에서부터 최대 7일간 탐색하며 채우고, Return은 0.0으로 대체"""
        if 'Coffee_Price' in df.columns:
            for shift_day in range(1, 8):
                df['Coffee_Price'] = df['Coffee_Price'].fillna(df['Coffee_Price'].shift(shift_day))

        return_cols = [col for col in df.columns if col.endswith('_Return')]
        df[return_cols] = df[return_cols].fillna(0.0)


        return df


    def _reduce_features(self, df: pd.DataFrame) -> pd.DataFrame:
        existing = [col for col in self.selected_features if col in df.columns]
        reduced_df = df[existing].copy()

        # season_tag, days_until_harvest 있으면 추가 보존
        for col in ['season_tag', 'days_until_harvest']:
            if col in df.columns and col not in reduced_df.columns:
                reduced_df[col] = df[col]

        return reduced_df

    def _add_derived_features(self, df: pd.DataFrame, country: str) -> pd.DataFrame:
        # 수확 시기
        df['Month'] = pd.to_datetime(df['Date']).dt.month.astype(int)
        df['season_tag'] = df['Month'].apply(lambda m: self._get_season_tag(m, country))
        df.drop(columns='Month', inplace=True)

        # 수확까지 남은 날짜
        harvest_start_month = {
            "brazil": 5,
            "colombia": 10,
            "ethiopia": 10
        }.get(country, 5)

        df['Date'] = pd.to_datetime(df['Date'])
        df['days_until_harvest'] = df['Date'].apply(
            lambda d: self._calculate_days_until_harvest(d, harvest_start_month)
        )

        # Lag feature 생성
        df.set_index('Date', inplace=True)
        for feature in ['T2M', 'WS2M', 'ALLSKY_SFC_SW_DWN', 'PRECTOTCORR']:
            for m in range(1, 7):
                df[f"{feature}_lag_{m}m"] = df[feature].shift(m * 30, freq='D')
        df.reset_index(inplace=True)

        return df

    def _get_season_tag(self, month: int, country: str) -> str:
        if country == 'brazil':
            if 5 <= month <= 9:
                return 'harvest'
            elif 3 <= month <= 4:
                return 'pre-harvest'
            else:
                return 'off-season'
        elif country == 'colombia':
            if month in [10, 11, 12, 1]:
                return 'harvest'
            elif month in [4, 5, 6]:
                return 'sub_harvest'
            elif month in [2, 3, 9]:
                return 'pre-harvest'
            else:
                return 'off-season'
        elif country == 'ethiopia':
            if month in [10, 11, 12, 1, 2]:
                return 'harvest'
            elif month in [8, 9]:
                return 'pre-harvest'
            else:
                return 'off-season'
        return 'off-season'

    def _calculate_days_until_harvest(self, date: pd.Timestamp, start_month: int) -> int:
        this_year = date.year
        next_harvest = pd.Timestamp(year=this_year, month=start_month, day=1)
        if date >= next_harvest:
            next_harvest = pd.Timestamp(year=this_year + 1, month=start_month, day=1)
        return (next_harvest - date).days


if __name__ == "__main__":
    selected_features = [
        'Date',
        'T2M',
        'WS2M',
        'ALLSKY_SFC_SW_DWN',
        'ALLSKY_SFC_UV_INDEX',
        'PRECTOTCORR',
        'RH2M',
        'PS',
        'Coffee_Price',
        'Coffee_Price_Return'
    ]

    processor = Preprocessor2(
        selected_features=selected_features,
        input_dir="../data/processed1",
        output_dir="../data/processed2"
    )
    processor.run_all()
