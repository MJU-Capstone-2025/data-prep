# merge_weather_data.py

import pandas as pd
import glob
import os

class WeatherDataMerger:
    def __init__(self, input_path="../data/processed2/*.csv", output_path="../data/final/merged_data.csv"):
        self.input_path = input_path
        self.output_path = output_path

    def run_all(self):
        files = glob.glob(self.input_path)
        if not files:
            print("❌ 병합할 파일이 없습니다.")
            return

        dataframes = []
        for file in files:
            df = pd.read_csv(file)
            dataframes.append(df)

        merged_df = pd.concat(dataframes, ignore_index=True)

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        merged_df.to_csv(self.output_path, index=False)

        print(f"✅ 병합 완료! 총 {len(files)}개 파일 → shape = {merged_df.shape}")
        print(f"📁 저장 위치: {self.output_path}")
