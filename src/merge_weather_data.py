import pandas as pd
import glob
import os
import os.path

class WeatherDataMerger:
    def __init__(
        self,
        input_path="../data/processed2/*.csv",
        output_path="../data/final/train_data.csv",
        test_output_path="../data/final/test_data.csv",
        test_only_price_output="../data/final/coffee_label.csv",
        test_start="2025-01-01",
        test_end="2025-04-01"
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.test_output_path = test_output_path
        self.test_only_price_output = test_only_price_output
        self.test_start = pd.to_datetime(test_start)
        self.test_end = pd.to_datetime(test_end)

    def run_all(self):
        files = glob.glob(self.input_path)
        if not files:
            print("❌ 병합할 파일이 없습니다.")
            return

        dataframes = []
        for file in files:
            df = pd.read_csv(file)

            # locationName 컬럼 추가
            location_name = os.path.splitext(os.path.basename(file))[0]
            df["locationName"] = location_name

            dataframes.append(df)

        merged_df = pd.concat(dataframes, ignore_index=True)

        if 'Date' not in merged_df.columns:
            print("❌ 'Date' 컬럼이 없습니다.")
            return

        # 날짜 변환 및 정렬
        merged_df["Date"] = pd.to_datetime(merged_df["Date"])
        merged_df = merged_df.sort_values("Date").reset_index(drop=True)

        # 테스트 기간 분리
        test_df = merged_df[(merged_df["Date"] >= self.test_start) & (merged_df["Date"] <= self.test_end)]
        train_df = merged_df[~((merged_df["Date"] >= self.test_start) & (merged_df["Date"] <= self.test_end))]

        # 학습용 데이터 저장
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        train_df.to_csv(self.output_path, index=False)
        print(f"✅ 학습용 병합 데이터 저장 완료 → shape = {train_df.shape}")
        print(f"📁 저장 위치: {self.output_path}")

        # 테스트 데이터 저장
        os.makedirs(os.path.dirname(self.test_output_path), exist_ok=True)
        test_df.to_csv(self.test_output_path, index=False)
        print(f"🧪 테스트셋 저장 완료 → 기간: {self.test_start.date()} ~ {self.test_end.date()} → shape = {test_df.shape}")
        print(f"📁 저장 위치: {self.test_output_path}")

        # 테스트 가격 데이터 저장
        price_cols = ["Date", "Coffee_Price", "Coffee_Price_Return"]
        if all(col in test_df.columns for col in price_cols):
            dedup_price_df = test_df[price_cols].drop_duplicates(subset=["Date"])
            dedup_price_df.to_csv(self.test_only_price_output, index=False)
            print(f"💰 테스트 가격 데이터 저장 완료 (중복 제거됨) → shape = {dedup_price_df.shape}")
            print(f"📁 저장 위치: {self.test_only_price_output}")
        else:
            print("⚠️ 'Coffee_Price' 또는 'Coffee_Return' 컬럼이 누락되었습니다.")

