import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import root_mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
import glob
import os

class XGBoostModel:
    def __init__(self, random_state=42):
        self.model = None
        self.random_state = random_state
        self.is_trained = False
        self.scaler = StandardScaler()

    def train(self, X_train, y_train, cat_features=None):
        y_scaled = self.scaler.fit_transform(y_train.values.reshape(-1, 1)).ravel()

        preprocessor = ColumnTransformer(
            transformers=[('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)],
            remainder='passthrough'
        )

        self.model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', XGBRegressor(
                random_state=self.random_state,
                n_estimators=300,
                max_depth=6,
                learning_rate=0.1,
                n_jobs=-1,
                verbosity=0
            ))
        ])

        self.model.fit(X_train, y_scaled)
        self.is_trained = True

    def predict(self, X):
        if not self.is_trained:
            raise Exception("Model has not been trained yet.")
        y_scaled_pred = self.model.predict(X)
        return self.scaler.inverse_transform(y_scaled_pred.reshape(-1, 1)).ravel()

    def evaluate(self, X_test, y_test):
        preds = self.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        return {"RMSE": rmse, "R2": r2}


class TestXGBmodel:
    def __init__(self):
        self.data = None
        self.model = None
        self.cat_features = []

    def load_datas(self, folder_glob_pattern):
        files = glob.glob(folder_glob_pattern)
        all_data = [pd.read_csv(f) for f in files]
        self.data = pd.concat(all_data, ignore_index=True)
        print(f"📄 총 데이터 로드 완료: {len(files)}개 파일, shape = {self.data.shape}")
        return self.data

    def run_training_pipeline(self, save_path="../data/test_pred_result/xgb/xgb_pred_result.csv"):
        df = self.data.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df = df.dropna()

        target_col = "Coffee_Return"
        exclude_cols = ["Date", "Coffee_Price", "Coffee_Return"]
        X = df[[col for col in df.columns if col not in exclude_cols]]
        y = df[target_col]

        self.cat_features = ['season_tag'] if 'season_tag' in X.columns else []

        split_idx = int(len(df) * 0.9)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        val_dates = df["Date"].iloc[split_idx:]
        val_prices = df["Coffee_Price"].iloc[split_idx:]

        self.model = XGBoostModel()
        self.model.train(X_train, y_train, cat_features=self.cat_features)
        preds = self.model.predict(X_val)

        results = pd.DataFrame({
            "Date": val_dates.values,
            "True_Coffee_Return": y_val.values,
            "Predicted_Coffee_Return": preds,
            "True_Coffee_Price": val_prices.values
        })

        predicted_prices = [val_prices.values[0]]
        for i in range(1, len(preds)):
            prev_price = val_prices.values[i - 1]
            predicted_prices.append(prev_price * (1 + preds[i]))
        results["Predicted_Coffee_Price"] = predicted_prices

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        results.to_csv(save_path, index=False)
        print(f"✅ 결과 저장 완료: {save_path}")

        scores = self.model.evaluate(X_val, y_val)
        print("📊 평가 결과 (XGBoost):")
        print(f"RMSE: {scores['RMSE']:.4f}")
        print(f"R2  : {scores['R2']:.4f}")

        self._plot_prediction(results, save_path.replace(".csv", "_plot.png"))

    def predict_future_until(self, start_date: str, end_date: str, save_path="../data/test_pred_result/xgb/xgb_future_pred.csv"):
        df = self.data.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df = df.dropna()

        df_latest = df[df["Date"] <= pd.to_datetime(start_date)].copy()
        last_known_price = df_latest.iloc[-1]["Coffee_Price"]

        future_dates = pd.date_range(start=start_date, end=end_date)
        predictions = []

        for date in future_dates:
            last_row = df_latest.iloc[-1:].copy()
            new_row = last_row.copy()
            new_row["Date"] = date

            for feature in ["T2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"]:
                for m in range(6, 1, -1):
                    new_row[f"{feature}_lag_{m}m"] = new_row[f"{feature}_lag_{m - 1}m"].values[0]
                new_row[f"{feature}_lag_1m"] = last_row[feature].values[0]

            input_row = new_row.drop(columns=["Date", "Coffee_Price", "Coffee_Return"])
            pred_return = self.model.predict(input_row.iloc[0:1])[0]
            predicted_price = last_known_price * (1 + pred_return)

            new_row["Coffee_Return"] = pred_return
            new_row["Coffee_Price"] = predicted_price
            last_known_price = predicted_price

            df_latest = pd.concat([df_latest, new_row], ignore_index=True)

            predictions.append({
                "Date": date,
                "Predicted_Coffee_Return": pred_return,
                "Predicted_Coffee_Price": predicted_price
            })

        result_df = pd.DataFrame(predictions)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        result_df.to_csv(save_path, index=False)
        print(f"📈 미래 예측 저장 완료: {save_path}")
        self._plot_prediction(result_df, save_path.replace(".csv", "_plot.png"), future=True)

    def _plot_prediction(self, df, filename, future=False):
        plt.figure(figsize=(14, 6))
        if future:
            plt.plot(df["Date"], df["Predicted_Coffee_Price"], label="Predicted Future Price", color="green", linestyle="--")
            plt.title("📈 Predicted Future Coffee Price")
            plt.ylabel("Coffee Price (cents/lb)")
        else:
            plt.subplot(2, 1, 1)
            plt.plot(df["Date"], df["True_Coffee_Price"], label="True Price", color="black", linewidth=2)
            plt.plot(df["Date"], df["Predicted_Coffee_Price"], label="Predicted Price", color="orange", linestyle="--")
            plt.title("📈 True vs Predicted Coffee Price (Validation)")
            plt.ylabel("Coffee Price (cents/lb)")
            plt.legend()
            plt.grid(True)

            plt.subplot(2, 1, 2)
            residuals = df["Predicted_Coffee_Price"] - df["True_Coffee_Price"]
            plt.bar(df["Date"], residuals, color="red", alpha=0.6, label="Residual (Prediction - Truth)")
            plt.axhline(0, color='black', linewidth=0.8)
            plt.title("📉 Prediction Error (Residual)")
            plt.ylabel("Prediction Error")
            plt.grid(True)
            plt.legend()

        plt.xlabel("Date")
        plt.tight_layout()
        plt.savefig(filename)
        print(f"🖼️ 그래프 저장 완료: {filename}")


if __name__ == "__main__":
    tester = TestXGBmodel()
    tester.load_datas("../data/processed2/*.csv")
    tester.run_training_pipeline()
    tester.predict_future_until("2025-04-01", "2026-04-01")
