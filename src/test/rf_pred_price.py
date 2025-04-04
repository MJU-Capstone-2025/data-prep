import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import os

class RandomForestModel:
    def __init__(self, random_state=42):
        """RandomForest 모델 클래스 초기화."""
        self.model = None
        self.random_state = random_state
        self.is_trained = False
        self.scaler = StandardScaler()

    def train(self, X_train, y_train, cat_features=None):
        """모델 학습. 타겟(y)은 스케일링 후 학습에 사용됨."""
        y_scaled = self.scaler.fit_transform(y_train.values.reshape(-1, 1)).ravel()
        preprocessor = ColumnTransformer(
            transformers=[('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)],
            remainder='passthrough'
        )
        self.model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', RandomForestRegressor(
                random_state=self.random_state,
                max_features='sqrt',
                n_estimators=300,
                n_jobs=-1
            ))
        ])
        self.model.fit(X_train, y_scaled)
        self.is_trained = True

    def predict(self, X):
        """모델 예측. 예측 결과는 스케일링 복원됨."""
        if not self.is_trained:
            raise Exception("Model has not been trained yet.")
        y_scaled_pred = self.model.predict(X)
        return self.scaler.inverse_transform(y_scaled_pred.reshape(-1, 1)).ravel()

    def evaluate(self, X_test, y_test):
        """모델 성능 평가 (RMSE 및 R2)"""
        preds = self.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        return {"RMSE": rmse, "R2": r2}


class TestRFmodel:
    def __init__(self):
        """RandomForest 테스트 클래스 초기화"""
        self.data = None
        self.model = None
        self.cat_features = []

    def load_datas(self, filepath="../data/final/train_weather.csv"):
        """학습 및 예측에 사용할 데이터를 로드."""
        self.data = pd.read_csv(filepath)
        print(f"📄 데이터 로드 완료: shape = {self.data.shape}")
        return self.data

    def run_training_pipeline(self, save_path="../data/test_pred_result/rf/rf_price_pred_result.csv"):
        """학습 파이프라인 실행. 예측 결과 및 검증 결과 저장."""
        df = self.data.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True).dropna()

        target_col = "Coffee_Price"
        exclude_cols = ["Date", "Coffee_Price", "Coffee_Return"]
        X = df[[col for col in df.columns if col not in exclude_cols]]
        y = df[target_col]

        self.cat_features = [col for col in ['season_tag', 'locationName'] if col in X.columns]

        split_idx = int(len(df) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        val_dates = df["Date"].iloc[split_idx:]

        self.model = RandomForestModel()
        self.model.train(X_train, y_train, cat_features=self.cat_features)
        preds = self.model.predict(X_val)

        results = pd.DataFrame({
            "Date": val_dates.values,
            "True_Coffee_Price": y_val.values,
            "Predicted_Coffee_Price": preds
        })

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        results.to_csv(save_path, index=False)
        print(f"✅ 결과 저장 완료: {save_path}")

        scores = self.model.evaluate(X_val, y_val)
        print("📊 평가 결과:")
        print(f"RMSE: {scores['RMSE']:.4f}")
        print(f"R2  : {scores['R2']:.4f}")

        self._plot_prediction(results, save_path.replace(".csv", "_plot.png"))

    def predict_future_until(self, start_date: str, end_date: str, save_path="../data/test_pred_result/rf/future_price_pred.csv"):
        """2024-12-31까지 데이터를 바탕으로 미래 구간의 커피 가격 예측."""
        df = self.data.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True).dropna()

        df_latest = df[df["Date"] <= pd.to_datetime("2024-12-31")].copy()
        last_known_price = df_latest.iloc[-1]["Coffee_Price"]
        country = self._detect_country(df_latest)

        future_dates = pd.date_range(start=start_date, end=end_date)
        predictions = []

        for date in future_dates:
            last_row = df_latest.iloc[-1:].copy()
            new_row = last_row.copy()
            new_row["Date"] = date
            new_row["days_until_harvest"] = self._days_until_harvest(date, country)
            new_row["season_tag"] = self._get_season_tag(date.month, country)

            for feature in ["T2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"]:
                for m in range(6, 1, -1):
                    new_row[f"{feature}_lag_{m}m"] = new_row[f"{feature}_lag_{m - 1}m"].values[0]
                new_row[f"{feature}_lag_1m"] = last_row[feature].values[0]

            input_row = new_row.drop(columns=["Date", "Coffee_Price", "Coffee_Return"])
            pred_price = self.model.predict(input_row.iloc[0:1])[0]

            new_row["Coffee_Price"] = pred_price
            df_latest = pd.concat([df_latest, new_row], ignore_index=True)

            predictions.append({
                "Date": date,
                "Predicted_Coffee_Price": pred_price
            })

        result_df = pd.DataFrame(predictions)

        try:
            label_df = pd.read_csv("../data/final/coffee_label.csv")
            label_df["Date"] = pd.to_datetime(label_df["Date"])
            compare_df = label_df[label_df["Date"].isin(result_df["Date"])]
            result_df = pd.merge(result_df, compare_df[["Date", "Coffee_Price"]].rename(columns={"Coffee_Price": "True_Future_Coffee_Price"}), on="Date", how="left")
        except Exception as e:
            print(f"⚠️ 실제 커피 가격 불러오기 실패: {e}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        result_df.to_csv(save_path, index=False)
        print(f"📈 미래 예측 저장 완료: {save_path}")
        self._plot_prediction(result_df, save_path.replace(".csv", "_plot.png"), future=True)

    def _days_until_harvest(self, date: pd.Timestamp, country: str) -> int:
        """수확까지 남은 일 수 계산."""
        harvest_month = {"brazil": 5, "colombia": 10, "ethiopia": 10}.get(country.lower(), 5)
        next_harvest = pd.Timestamp(year=date.year + (date.month >= harvest_month), month=harvest_month, day=1)
        return (next_harvest - date).days

    def _get_season_tag(self, month: int, country: str) -> str:
        """나라별 월 기준 시즌 태그 반환."""
        country = country.lower()
        if country == 'brazil':
            return 'harvest' if 5 <= month <= 9 else 'pre-harvest' if 3 <= month <= 4 else 'off-season'
        if country == 'colombia':
            return 'harvest' if month in [10,11,12,1] else 'sub_harvest' if month in [4,5,6] else 'pre-harvest' if month in [2,3,9] else 'off-season'
        if country == 'ethiopia':
            return 'harvest' if month in [10,11,12,1,2] else 'pre-harvest' if month in [8,9] else 'off-season'
        return 'off-season'

    def _detect_country(self, df: pd.DataFrame) -> str:
        """기본 국가 추정 (현재는 brazil 고정)."""
        return "brazil"

    def _plot_prediction(self, df, filename, future=False):
        """예측 결과 시각화 및 저장."""
        plt.figure(figsize=(14, 6))
        if future:
            plt.plot(df["Date"], df["Predicted_Coffee_Price"], label="Predicted Future Price", color="green", linestyle="--")
            if "True_Future_Coffee_Price" in df.columns:
                plt.plot(df["Date"], df["True_Future_Coffee_Price"], label="True Future Price", color="black", linewidth=2)
            plt.title("Predicted Future Coffee Price vs True Price")
            plt.ylabel("Coffee Price (cents/lb)")
            plt.legend()
            plt.grid(True)
        else:
            plt.subplot(2, 1, 1)
            plt.plot(df["Date"], df["True_Coffee_Price"], label="True Price", color="black", linewidth=2)
            plt.plot(df["Date"], df["Predicted_Coffee_Price"], label="Predicted Price", color="orange", linestyle="--")
            plt.title("True vs Predicted Coffee Price (Validation)")
            plt.ylabel("Coffee Price (cents/lb)")
            plt.legend()
            plt.grid(True)

            plt.subplot(2, 1, 2)
            residuals = df["Predicted_Coffee_Price"] - df["True_Coffee_Price"]
            plt.bar(df["Date"], residuals, color="red", alpha=0.6, label="Residual (Prediction - Truth)")
            plt.axhline(0, color='black', linewidth=0.8)
            plt.title("Prediction Error (Residual)")
            plt.ylabel("Prediction Error")
            plt.grid(True)
            plt.legend()

        plt.xlabel("Date")
        plt.tight_layout()
        plt.savefig(filename)
        print(f"🖼️ 그래프 저장 완료: {filename}")


if __name__ == "__main__":
    tester = TestRFmodel()
    tester.load_datas("../data/final/train_weather.csv")
    tester.run_training_pipeline()
    tester.predict_future_until("2025-01-01", "2025-04-01")
