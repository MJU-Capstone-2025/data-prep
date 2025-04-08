import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
import os

class RandomForestModel:
    def __init__(self, random_state=42):
        self.model = None
        self.random_state = random_state
        self.is_trained = False

    def train(self, X_train, y_train, cat_features=None):
        y_train_scaled = y_train * 100
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
        self.model.fit(X_train, y_train_scaled)
        self.is_trained = True

    def predict(self, X, alpha=1.0):
        if not self.is_trained:
            raise Exception("Model has not been trained yet.")
        y_pred_scaled = self.model.predict(X)
        return (y_pred_scaled / 100) * alpha

    def evaluate(self, X_test, y_test, alpha=1.0):
        preds = self.predict(X_test, alpha=alpha)
        rmse = mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        return {"RMSE": rmse, "R2": r2}

class Testmodel:
    def __init__(self):
        self.data = None
        self.model = None
        self.cat_features = []

    def load_datas(self, filepath="../data/final/train_weather.csv"):
        self.data = pd.read_csv(filepath)
        print(f"📄 데이터 로드 완료: shape = {self.data.shape}")
        return self.data

    def run_training_pipeline(self, save_path="../data/test_pred_result/rf/rf_pred_result_v2.csv", alpha=5.0):
        df = self.data.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True).dropna()

        target_col = "Coffee_Return"
        exclude_cols = ["Date", "Coffee_Price", "Coffee_Return"]
        X = df[[col for col in df.columns if col not in exclude_cols]]
        y = df[target_col]

        self.cat_features = [col for col in ['season_tag', 'locationName'] if col in X.columns]

        split_idx = int(len(df) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        val_dates = df["Date"].iloc[split_idx:]
        val_prices = df["Coffee_Price"].iloc[split_idx:]

        self.model = RandomForestModel()
        self.model.train(X_train, y_train, cat_features=self.cat_features)
        preds = self.model.predict(X_val, alpha=alpha)

        results = pd.DataFrame({
            "Date": val_dates.values,
            "True_Coffee_Return": y_val.values,
            "Predicted_Coffee_Return": preds,
            "True_Coffee_Price": val_prices.values
        })

        daily_return = results.groupby("Date").agg({
            "True_Coffee_Return": "mean",
            "Predicted_Coffee_Return": "mean",
            "True_Coffee_Price": "first"
        }).reset_index()

        predicted_prices = [daily_return["True_Coffee_Price"].iloc[0]]
        for i in range(1, len(daily_return)):
            prev_price = predicted_prices[-1]
            predicted_prices.append(prev_price * (1 + daily_return["Predicted_Coffee_Return"].iloc[i]))
        daily_return["Predicted_Coffee_Price"] = predicted_prices

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        daily_return.to_csv(save_path, index=False)
        print(f"✅ 결과 저장 완료: {save_path}")

        X_val_grouped = X_val.copy()
        X_val_grouped["Date"] = val_dates.values
        numeric_cols = X_val_grouped.select_dtypes(include=["number"]).columns
        X_val_numeric = X_val_grouped.groupby("Date")[numeric_cols].mean().reset_index()
        cat_cols = ["season_tag", "locationName"]
        X_val_cat = X_val_grouped.groupby("Date")[cat_cols].first().reset_index()
        X_val_final = pd.merge(X_val_numeric, X_val_cat, on="Date", how="left")
        y_val_grouped = daily_return["True_Coffee_Return"]

        scores = self.model.evaluate(X_val_final.drop(columns=["Date"]), y_val_grouped, alpha=alpha)
        print("📊 평가 결과:")
        print(f"RMSE: {scores['RMSE']:.4f}")
        print(f"R2  : {scores['R2']:.4f}")

        self._plot_prediction(daily_return, save_path.replace(".csv", "_plot.png"))

        # 초반 5개월짜리만 시각화 따로 저장
        first_5m = daily_return[daily_return['Date'] < daily_return['Date'].min() + pd.DateOffset(months=5)]
        self._plot_prediction(first_5m, save_path.replace(".csv", "_first5m_plot.png"))

    def predict_future_until(self, start_date: str, end_date: str, save_path="../data/test_pred_result/rf/future_pred_v2.csv", alpha=5.0):
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
            pred_return = self.model.predict(input_row.iloc[0:1], alpha=alpha)[0]
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

        try:
            label_df = pd.read_csv("../data/final/coffee_label.csv")
            label_df["Date"] = pd.to_datetime(label_df["Date"])
            result_df = result_df.merge(
                label_df[["Date", "Coffee_Price"]].rename(columns={"Coffee_Price": "True_Future_Price"}),
                on="Date", how="left"
            )
        except Exception as e:
            print(f"⚠️ 실제 커피 가격 병합 실패: {e}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        result_df.to_csv(save_path, index=False)
        print(f"📈 미래 예측 저장 완료: {save_path}")
        self._plot_prediction(result_df, save_path.replace(".csv", "_plot.png"), future=True)

    def _days_until_harvest(self, date: pd.Timestamp, country: str) -> int:
        country = country.lower()
        harvest_month = {"brazil": 5, "colombia": 10, "ethiopia": 10}.get(country, 5)
        this_year = date.year
        next_harvest = pd.Timestamp(year=this_year, month=harvest_month, day=1)
        if date >= next_harvest:
            next_harvest = pd.Timestamp(year=this_year + 1, month=harvest_month, day=1)
        return (next_harvest - date).days

    def _get_season_tag(self, month: int, country: str) -> str:
        country = country.lower()
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

    def _detect_country(self, df: pd.DataFrame) -> str:
        return "brazil"

    def _plot_prediction(self, df, filename, future=False):
        plt.figure(figsize=(14, 6))
        if future:
            plt.plot(df["Date"], df["Predicted_Coffee_Price"], label="Predicted Future Price", color="green", linestyle="--")
            if "True_Future_Price" in df.columns:
                plt.plot(df["Date"], df["True_Future_Price"], label="True Future Price", color="black", linewidth=2)
            plt.title("Predicted vs True Future Coffee Price")
            plt.ylabel("Coffee Price (cents/lb)")
            plt.legend()
            plt.grid(True)
        else:
            plt.subplot(2, 1, 1)
            plt.plot(df["Date"], df["True_Coffee_Price"], label="True Price", color="black", linewidth=2)
            plt.plot(df["Date"], df["Predicted_Coffee_Price"], label="Predicted Price", color="orange", linestyle="--")
            plt.title("Validation: True vs Predicted Coffee Price")
            plt.ylabel("Coffee Price (cents/lb)")
            plt.legend()
            plt.grid(True)

            plt.subplot(2, 1, 2)
            residuals = df["Predicted_Coffee_Price"] - df["True_Coffee_Price"]
            plt.bar(df["Date"], residuals, color="red", alpha=0.6)
            plt.axhline(0, color='black', linewidth=0.8)
            plt.title("Prediction Residuals")
            plt.ylabel("Residual")
            plt.grid(True)
        plt.xlabel("Date")
        plt.tight_layout()
        plt.savefig(filename)
        print(f"🖼️ 그래프 저장 완료: {filename}")

if __name__ == "__main__":
    tester = Testmodel()
    tester.load_datas("../data/final/train_weather.csv")
    tester.run_training_pipeline(alpha=10)
    tester.predict_future_until("2025-01-01", "2025-04-01", alpha=10)
