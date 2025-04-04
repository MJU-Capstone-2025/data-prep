import pandas as pd
import os

class WeatherCoffeeMerger:
    def __init__(self, weather_path=None, coffee_path=None, output_path=None):
        self.weather_path = weather_path
        self.coffee_path = coffee_path
        self.output_path = output_path
        self.weather_df = None
        self.coffee_df = None
        self.merged_df = None

    def load_data(self):
        try:
            self.weather_df = pd.read_csv(self.weather_path)
            self.coffee_df = pd.read_csv(self.coffee_path)

            self.weather_df['Date'] = pd.to_datetime(self.weather_df['Date'])
            self.coffee_df['Date'] = pd.to_datetime(self.coffee_df['Date'])

            print("📥 데이터 로드 완료")
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")

    def merge_on_date(self):
        if self.weather_df is not None and self.coffee_df is not None:
            self.merged_df = pd.merge(self.weather_df, self.coffee_df, on='Date', how='outer')
            print(f"🔗 병합 완료: {len(self.merged_df)}개 날짜 기준")
        else:
            print("⚠ 데이터가 비어있어 병합할 수 없습니다.")

    def save_merged(self):
        if self.merged_df is not None and not self.merged_df.empty:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            self.merged_df.to_csv(self.output_path, index=False)
            print(f"✅ 병합된 데이터 저장 완료: {self.output_path}")
        else:
            print("❌ 저장할 병합 데이터가 없습니다.")

    def run_all(self, coffee_path="../data/processed1/coffee_c_price.csv", input_dir="../data/processed1"):
        weather_files = [
            "brazil_carmo_de_minas",
            "brazil_patrocinio",
            "brazil_varginha",
            "colombia_armenia",
            "colombia_manizales",
            "colombia_pereira",
            "ethiopia_limu",
            "ethiopia_sidamo",
            "ethiopia_yirgacheffe"
        ]

        for name in weather_files:
            self.weather_path = f"{input_dir}/{name}.csv"
            self.coffee_path = coffee_path
            self.output_path = f"{input_dir}/{name}.csv"

            print(f"\n🌀 병합 시작: {self.weather_path}")
            self.load_data()
            self.merge_on_date()
            self.save_merged()
